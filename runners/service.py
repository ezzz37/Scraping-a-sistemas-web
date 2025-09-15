from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path

from core.parse import load_urls, fetch, parse_page
from core.crawl import crawl as legacy_crawl

app = FastAPI()

class CrawlReq(BaseModel):
    start_url: str
    depth: int = 2
    delay: float = 0.75
    out: str = "data/peugeot_urls.json"

class ScrapeReq(BaseModel):
    urls_file: str = "data/peugeot_urls.json"

@app.post("/crawl")
def crawl_ep(req: CrawlReq):
    global START_URL, MAX_DEPTH, DELAY_S
    START_URL, MAX_DEPTH, DELAY_S = req.start_url, req.depth, req.delay
    legacy_crawl(MAX_DEPTH, DELAY_S)
    data = json.loads(Path("peugeot_urls.json").read_text(encoding="utf-8"))
    Path(req.out).parent.mkdir(parents=True, exist_ok=True)
    Path(req.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"saved": req.out, "count": data.get("count", len(data.get("urls", [])))}

@app.post("/scrape")
def scrape_ep(req: ScrapeReq):
    urls = load_urls(req.urls_file)
    out = []
    for u in urls:
        status, html, hdrs = fetch(u)
        if html:
            row = parse_page(u, html, hdrs)
            row["status_code"] = status
            out.append(row)
    return {"count": len(out), "items": out}
