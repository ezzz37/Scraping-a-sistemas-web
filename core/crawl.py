import re
import time
import csv
import json
import random
from urllib.parse import urljoin, urlparse
from urllib import robotparser
from collections import deque

import requests
from bs4 import BeautifulSoup


START_URL = "https://www.peugeot.com.ar/"
EXTRA_SEEDS = []
MAX_DEPTH = 2
DELAY_S = 0.75
CONCURRENCY = 1
USER_AGENT = "Mozilla/5.0 (+crawler demo; https://example.org/contact)"

def _origin_of(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"

ORIGIN = _origin_of(START_URL)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}
SEEN, RESULTS = set(), set()

# robots.txt
rp = robotparser.RobotFileParser()
try:
    rp.set_url(urljoin(ORIGIN, "/robots.txt"))
    rp.read()
except Exception:
    pass

NON_HTML_EXT_RE = re.compile(
    r"\.(?:png|jpe?g|gif|svg|webp|avif|ico|bmp|tiff|pdf|css|js|map|json|txt|csv|"
    r"woff2?|ttf|otf|eot|mp4|mp3|mov|webm|zip|rar|7z)(?:\?|$)",
    re.IGNORECASE,
)

def is_same_origin(abs_url: str) -> bool:
    p = urlparse(abs_url)
    return f"{p.scheme}://{p.netloc}" == ORIGIN

def norm(u: str, base: str | None = None) -> str | None:
    try:
        if not u or u.startswith(("javascript:", "mailto:", "tel:")):
            return None
        absu = urljoin(base or ORIGIN, u)
        if not is_same_origin(absu):
            return None
        absu = absu.split("#", 1)[0]
        if NON_HTML_EXT_RE.search(absu):
            return None
        return absu
    except Exception:
        return None

def extract_links(html: str, base: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        u = norm(a["href"], base)
        if u:
            RESULTS.add(u)
    for link in soup.find_all("link", href=True):
        u = norm(link["href"], base)
        if u:
            RESULTS.add(u)

def allowed_by_robots(url: str) -> bool:
    try:
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True

def fetch(url: str, retries: int = 3, backoff: float = 1.3) -> str:
    if not allowed_by_robots(url):
        return ""
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code >= 400:
                return ""
            ct = (r.headers.get("content-type", "") or "").lower()
            text = r.text
            if ("html" not in ct) and ("<html" not in text.lower()):
                return ""
            return text
        except requests.RequestException:
            time.sleep((backoff ** i) + random.uniform(0, 0.3))
    return ""

def crawl(max_depth: int = MAX_DEPTH, delay: float = DELAY_S) -> None:
    seeds = [START_URL, *EXTRA_SEEDS]
    q = deque([(s, 0) for s in seeds if norm(s)])
    while q:
        url, d = q.popleft()
        if url in SEEN or d > max_depth:
            continue
        SEEN.add(url)

        html = fetch(url)
        if not html:
            time.sleep(delay)
            continue

        extract_links(html, url)

        if d < max_depth:
            frontier = [u for u in list(RESULTS) if u not in SEEN]
            for u in frontier:
                q.append((u, d + 1))

        time.sleep(delay)


def run(start_url: str, extra_seeds=None, max_depth: int = 2, delay: float = 0.75):
    global START_URL, EXTRA_SEEDS, MAX_DEPTH, DELAY_S, ORIGIN, rp
    START_URL = start_url
    EXTRA_SEEDS = extra_seeds or []
    MAX_DEPTH = max_depth
    DELAY_S = delay
    ORIGIN = _origin_of(START_URL)

    SEEN.clear()
    RESULTS.clear()

    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(urljoin(ORIGIN, "/robots.txt"))
        rp.read()
    except Exception:
        pass

    crawl(MAX_DEPTH, DELAY_S)
    return sorted(RESULTS)
