# Scraping-a-sistemas-web
Es un algoritmo de scraping que se ejecuta en un entorno virtual para ayuadr a scrapear webs


scrape general con la url parametrizada
python -m runners.cli crawl --start-url "https://www.peugeot.com.ar" --depth 2 --out data/peugeot_urls.json

Scrape → genera data/peugeot_pages.jsonl y data/peugeot_pages.csv
