import csv
import json
import random
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import requests
from bs4 import BeautifulSoup, Comment

# ========= Config por defecto (se puede sobreescribir) =========
# Si tus URLs son de otro dominio, no pasa nada: ORIGIN se ajusta
# automáticamente en load_urls() a partir de la primera URL válida.
ORIGIN = "https://www.peugeot.com.ar"
USER_AGENT = "Mozilla/5.0 (+scraper demo; https://example.org/contact)"
DELAY_S = 0.8
RETRIES = 3
BACKOFF = 1.35

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

# ========= Utilidades =========
def _origin_of(u: str) -> str:
    p = urlparse(u)
    return f"{p.scheme}://{p.netloc}"

def _same_origin(u: str, origin: str) -> bool:
    try:
        pu = urlparse(u)
        return f"{pu.scheme}://{pu.netloc}" == origin
    except Exception:
        return False

# ========= Cargar URLs (JSON o CSV) =========
def load_urls(path: str) -> list[str]:
    """
    Carga URLs desde:
      - JSON: {"urls":[...]} o lista simple
      - CSV:  columna 'url'
    Ajusta ORIGIN al de la primera URL encontrada y filtra por ese dominio.
    """
    global ORIGIN

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe {path}. Generá primero peugeot_urls.json/csv")

    urls: list[str] = []
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "urls" in data:
            urls = data["urls"]
        elif isinstance(data, list):
            urls = data
    else:
        # CSV con columna 'url'
        with p.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                u = (row.get("url") or "").strip()
                if u:
                    urls.append(u)

    # Ajustar ORIGIN según la primera URL válida
    for u in urls:
        try:
            ORIGIN = _origin_of(u)
            break
        except Exception:
            continue

    # Filtrar por el mismo dominio + normalizar sin fragmento
    cleaned = []
    for u in urls:
        if _same_origin(u, ORIGIN):
            cleaned.append(u.split("#")[0])

    # deduplicado + orden
    return sorted(set(cleaned))

# ========= HTTP con retries/backoff =========
def fetch(url: str) -> tuple[int, str, dict]:
    """
    Devuelve (status_code, text, headers) con retries + backoff y validación básica de HTML.
    """
    last_exc = None
    for i in range(RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code >= 400:
                return r.status_code, "", dict(r.headers or {})
            ct = (r.headers.get("content-type", "") or "").lower()
            text = r.text
            # Aceptar si parece HTML
            if "html" not in ct and "<html" not in text.lower():
                return r.status_code, "", dict(r.headers or {})
            return r.status_code, text, dict(r.headers or {})
        except requests.RequestException as e:
            last_exc = e
            time.sleep((BACKOFF ** i) + random.uniform(0, 0.3))
    # agotado
    return 0, "", {}

# ========= Helpers de parsing =========
def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def visible_text_nodes(soup: BeautifulSoup):
    """Itera nodos de texto visibles (excluye scripts, styles, nav, header, footer, comments)."""
    blacklist = {"script", "style", "noscript", "template", "svg"}
    for elem in soup.find_all(string=True):
        if isinstance(elem, Comment):
            continue
        parent = elem.parent
        if not parent:
            continue
        tag = (parent.name or "").lower()
        if tag in blacklist or tag in {"header", "nav", "footer", "aside"}:
            continue
        txt = clean_text(elem)
        if txt:
            yield txt

def pick_primary_block(soup: BeautifulSoup) -> str:
    """
    Heurística simple:
    1) si hay <main> o <article>, usar el que más texto visible tenga
    2) sino, <section>, y como fallback top divs
    """
    candidates = []
    def text_len(node):
        return len(" ".join(clean_text(t) for t in node.stripped_strings))

    for tag in soup.find_all(["main", "article"]):
        candidates.append((text_len(tag), tag))
    if not candidates:
        for tag in soup.find_all(["section"]):
            candidates.append((text_len(tag), tag))
    if not candidates:
        divs = sorted(((text_len(d), d) for d in soup.find_all("div")), key=lambda x: x[0], reverse=True)[:10]
        candidates.extend(divs)

    if not candidates:
        body = soup.body or soup
        text = " ".join(visible_text_nodes(body))
        return clean_text(text)

    best = max(candidates, key=lambda x: x[0])[1]
    for bad in best.find_all(["nav", "header", "footer", "aside"]):
        bad.decompose()
    text = " ".join(visible_text_nodes(best))
    return clean_text(text)

def extract_json_ld(soup: BeautifulSoup) -> list[str]:
    types = []
    for tag in soup.find_all("script", type=lambda v: v and "ld+json" in v.lower()):
        try:
            data = json.loads(tag.string or "{}")
        except Exception:
            continue
        def collect_types(obj):
            if isinstance(obj, dict):
                t = obj.get("@type")
                if isinstance(t, list):
                    for ti in t:
                        types.append(str(ti))
                elif isinstance(t, str):
                    types.append(t)
                for v in obj.values():
                    collect_types(v)
            elif isinstance(obj, list):
                for it in obj:
                    collect_types(it)
        collect_types(data)
    return sorted({t for t in types if t})

# ========= Parseo de una página =========
def parse_page(url: str, html: str, headers: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = clean_text(soup.title.string if soup.title else "")
    # meta description
    md = soup.find("meta", attrs={"name": "description"})
    meta_description = clean_text(md["content"]) if md and md.has_attr("content") else ""
    # h1
    h1 = soup.find("h1")
    h1_text = clean_text(h1.get_text(" ")) if h1 else ""
    # canonical
    link_canon = soup.find("link", rel=lambda v: v and "canonical" in v.lower())
    canonical = clean_text(link_canon["href"]) if link_canon and link_canon.has_attr("href") else ""
    if canonical and canonical.startswith("/"):
        canonical = urljoin(url, canonical)

    # OpenGraph
    def og(name):
        tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
        return clean_text(tag["content"]) if tag and tag.has_attr("content") else ""
    og_title = og("og:title")
    og_desc  = og("og:description")
    og_image = og("og:image")
    if og_image and og_image.startswith("/"):
        og_image = urljoin(url, og_image)

    # JSON-LD types
    ld_types = extract_json_ld(soup)

    # Texto principal
    primary_text = pick_primary_block(soup)
    words = len(primary_text.split())
    if len(primary_text) > 1200:
        primary_text = primary_text[:1200].rsplit(" ", 1)[0] + "…"

    # Conteo de enlaces
    internal, external = 0, 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue
        absu = urljoin(url, href)
        if urlparse(absu).netloc == urlparse(ORIGIN).netloc:
            internal += 1
        else:
            external += 1

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "h1": h1_text,
        "canonical": canonical,
        "og_title": og_title,
        "og_description": og_desc,
        "og_image": og_image,
        "ld_json_types": ld_types,
        "primary_text": primary_text,
        "word_count": words,
        "links_internal": internal,
        "links_external": external,
    }
