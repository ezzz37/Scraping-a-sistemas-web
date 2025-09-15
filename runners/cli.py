import argparse
import json
from pathlib import Path

from core import crawl as crawl_mod
from core import parse as parse_mod


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def cmd_crawl(start_url: str, depth: int, delay: float, out_json: Path) -> None:
    """
    Ejecuta el crawler y guarda la salida en out_json con forma
    {"count": N, "urls": [...]}
    """
    urls = crawl_mod.run(start_url=start_url, extra_seeds=None, max_depth=depth, delay=delay)

    ensure_parent(out_json)
    payload = {"count": len(urls), "urls": urls}
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"saved": str(out_json), "count": len(urls)}, ensure_ascii=False))


def cmd_scrape(urls_file: Path, out_jsonl: Path | None, out_csv: Path | None) -> None:
    urls = parse_mod.load_urls(str(urls_file))
    rows = []

    jf = out_jsonl.open("w", encoding="utf-8") if out_jsonl else None
    try:
        for u in urls:
            status, html, hdrs = parse_mod.fetch(u)
            if not html:
                continue
            row = parse_mod.parse_page(u, html, hdrs)
            row["status_code"] = status
            rows.append(row)
            if jf:
                jf.write(json.dumps(row, ensure_ascii=False) + "\n")
    finally:
        jf.close() if jf else None

    if out_csv:
        import csv
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "url", "status_code",
            "title", "meta_description", "h1", "canonical",
            "og_title", "og_description", "og_image",
            "ld_json_types", "word_count",
            "links_internal", "links_external",
            "primary_text",
        ]
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                r2 = r.copy()
                if isinstance(r2.get("ld_json_types"), list):
                    r2["ld_json_types"] = ", ".join(r2["ld_json_types"])
                w.writerow(r2)

    print(json.dumps({"scraped": len(rows)}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(prog="runners.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("crawl", help="Crawlear sitio y guardar URLs")
    c.add_argument("--start-url", required=True)
    c.add_argument("--depth", type=int, default=2)
    c.add_argument("--delay", type=float, default=0.75)
    c.add_argument("--out", default="data/peugeot_urls.json")

    s = sub.add_parser("scrape", help="Scrapear URLs a JSONL/CSV")
    s.add_argument("--urls-file", default="data/peugeot_urls.json")
    s.add_argument("--out-jsonl", default="data/peugeot_pages.jsonl")
    s.add_argument("--out-csv", default="data/peugeot_pages.csv")

    args = ap.parse_args()
    if args.cmd == "crawl":
        cmd_crawl(args.start_url, args.depth, args.delay, Path(args.out))
    elif args.cmd == "scrape":
        out_jsonl = Path(args.out_jsonl) if args.out_jsonl else None
        out_csv = Path(args.out_csv) if args.out_csv else None
        cmd_scrape(Path(args.urls_file), out_jsonl, out_csv)


if __name__ == "__main__":
    main()
