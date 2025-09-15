### infraestructura base

scraper/
  core/
    __init__.py
    crawl.py          # (de tu crawl_peugeot.py pero sin I/O a disco)
    parse.py          # (de tu scrape_relevant_peugeot.py: parse_page, helpers)
    http.py           # requests.Session, headers, retries, proxy, timeouts
    robots.py
  runners/
    cli.py            # CLI con argparse: crawl, scrape, crawl+scrape
    service.py        # FastAPI con /crawl y /scrape
  io/
    storage.py        # S3/Dynamo/FS; JSONL/CSV streaming
    models.py         # Pydantic para inputs/outputs
requirements.txt
.env.example
