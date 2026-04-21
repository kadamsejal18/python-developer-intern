
# ─────────────────────────────────────────────
#  SECTION 1: BeautifulSoup Scraper
# ─────────────────────────────────────────────

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urljoin, urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ── Data Model ──────────────────────────────
@dataclass
class ScrapedArticle:
    title: str
    url: str
    author: Optional[str]
    date: Optional[str]
    summary: Optional[str]
    tags: List[str]


# ── BeautifulSoup Scraper Class ─────────────
class BeautifulSoupScraper:
    """
    A robust scraper using requests + BeautifulSoup.
    Handles pagination, retries, and polite delays.
    """

    def __init__(self, base_url: str, delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (compatible; PythonScraper/1.0; "
                "+https://example.com/bot)"
            )
        })

    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch a URL and return a BeautifulSoup object."""
        for attempt in range(1, retries + 1):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                time.sleep(self.delay)  # Polite crawling delay
                return BeautifulSoup(response.text, "html.parser")
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt}/{retries} failed for {url}: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
        logger.error(f"All retries exhausted for {url}")
        return None

    def extract_articles(self, soup: BeautifulSoup, page_url: str) -> List[ScrapedArticle]:
        """
        Extract articles from a page.
        Customize the CSS selectors below to match your target site.
        """
        articles = []

        # Example: scraping blog-style article cards
        for card in soup.select("article, .post-card, .article-item"):
            try:
                title_el = card.select_one("h1, h2, h3, .title, .post-title")
                link_el  = card.select_one("a[href]")
                author_el = card.select_one(".author, .byline, [rel='author']")
                date_el   = card.select_one("time, .date, .published")
                summary_el = card.select_one("p, .excerpt, .summary")
                tag_els   = card.select(".tag, .label, .category")

                article = ScrapedArticle(
                    title   = title_el.get_text(strip=True) if title_el else "N/A",
                    url     = urljoin(page_url, link_el["href"]) if link_el else page_url,
                    author  = author_el.get_text(strip=True) if author_el else None,
                    date    = date_el.get("datetime") or (date_el.get_text(strip=True) if date_el else None),
                    summary = summary_el.get_text(strip=True)[:200] if summary_el else None,
                    tags    = [t.get_text(strip=True) for t in tag_els],
                )
                articles.append(article)
            except Exception as e:
                logger.debug(f"Skipping card due to error: {e}")

        return articles

    def scrape_paginated(self, start_url: str, max_pages: int = 5) -> List[ScrapedArticle]:
        """Scrape multiple pages following pagination links."""
        all_articles = []
        current_url = start_url

        for page_num in range(1, max_pages + 1):
            logger.info(f"Scraping page {page_num}: {current_url}")
            soup = self.fetch_page(current_url)
            if not soup:
                break

            articles = self.extract_articles(soup, current_url)
            all_articles.extend(articles)
            logger.info(f"  → Found {len(articles)} articles on page {page_num}")

            # Find the "next" pagination link
            next_link = soup.select_one("a[rel='next'], .next-page a, .pagination .next")
            if not next_link or not next_link.get("href"):
                logger.info("No more pages found.")
                break
            current_url = urljoin(self.base_url, next_link["href"])

        return all_articles

    def scrape_single_article(self, url: str) -> dict:
        """Deep-scrape a single article page for full content."""
        soup = self.fetch_page(url)
        if not soup:
            return {}

        return {
            "url": url,
            "title": self._safe_text(soup, "h1"),
            "author": self._safe_text(soup, ".author, [rel='author']"),
            "published": self._safe_attr(soup, "time", "datetime"),
            "body": self._extract_body_text(soup),
            "images": self._extract_images(soup, url),
            "links": self._extract_links(soup, url),
        }

    # ── Helpers ──────────────────────────────
    def _safe_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    def _safe_attr(self, soup: BeautifulSoup, selector: str, attr: str) -> Optional[str]:
        el = soup.select_one(selector)
        return el.get(attr) if el else None

    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract clean body text, removing scripts and styles."""
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        body = soup.select_one("article, .post-content, .article-body, main")
        return body.get_text(separator="\n", strip=True) if body else ""

    def _extract_images(self, soup: BeautifulSoup, page_url: str) -> List[dict]:
        return [
            {"src": urljoin(page_url, img["src"]), "alt": img.get("alt", "")}
            for img in soup.find_all("img", src=True)
        ]

    def _extract_links(self, soup: BeautifulSoup, page_url: str) -> List[str]:
        base_domain = urlparse(page_url).netloc
        return list({
            urljoin(page_url, a["href"])
            for a in soup.find_all("a", href=True)
            if urlparse(urljoin(page_url, a["href"])).netloc == base_domain
        })


# ─────────────────────────────────────────────
#  SECTION 2: Scrapy Spider
# ─────────────────────────────────────────────
# To use Scrapy, install it: pip install scrapy
# Then run: scrapy runspider web_scraper.py -o output.json

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy import signals

    class ArticleSpider(scrapy.Spider):
        """
        A Scrapy spider for scraping article listings.
        Scrapy handles concurrency, rate limiting, and retries natively.
        """
        name = "article_spider"
        allowed_domains = ["quotes.toscrape.com"]  # ← Change to your target domain
        start_urls = ["https://quotes.toscrape.com"]  # ← Change to your start URL

        custom_settings = {
            "DOWNLOAD_DELAY": 1,        # Wait 1s between requests
            "CONCURRENT_REQUESTS": 4,   # Max parallel requests
            "ROBOTSTXT_OBEY": True,     # Respect robots.txt
            "LOG_LEVEL": "INFO",
            "FEEDS": {
                "scrapy_output.json": {"format": "json", "overwrite": True},
            },
        }

        def parse(self, response):
            """Parse article list page and follow links."""
            for article in response.css("article, .post-card"):
                yield {
                    "title":   article.css("h2, h3, .title::text").get("").strip(),
                    "url":     response.urljoin(article.css("a::attr(href)").get("")),
                    "summary": article.css("p, .excerpt::text").get("").strip(),
                    "tags": article.css(".tag::text").getall(),
                }

                # Follow article links for deep scraping
                detail_url = article.css("a::attr(href)").get()
                if detail_url:
                    yield response.follow(detail_url, callback=self.parse_article)

            # Follow pagination
            next_page = response.css("a[rel='next']::attr(href)").get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)

        def parse_article(self, response):
            """Deep-parse a single article page."""
            yield {
                "url":       response.url,
                "title":     response.css("h1::text").get("").strip(),
                "author":    response.css(".author::text, [rel='author']::text").get(""),
                "date":      response.css("time::attr(datetime)").get(""),
                "body":      " ".join(response.css("article p::text").getall()),
                "images": [
                    response.urljoin(src)
                    for src in response.css("article img::attr(src)").getall()
                ],
            }

    SCRAPY_AVAILABLE = True

except ImportError:
    SCRAPY_AVAILABLE = False
    logger.info("Scrapy not installed. Only BeautifulSoup scraper is available.")


# ─────────────────────────────────────────────
#  SECTION 3: Data Export Utilities
# ─────────────────────────────────────────────

class DataExporter:
    """Export scraped data to JSON or CSV."""

    @staticmethod
    def to_json(data: list, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) if hasattr(d, '__dataclass_fields__') else d
                       for d in data], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(data)} records to {filepath}")

    @staticmethod
    def to_csv(data: list, filepath: str):
        if not data:
            logger.warning("No data to export.")
            return
        rows = [asdict(d) if hasattr(d, '__dataclass_fields__') else d for d in data]
        # Flatten list fields
        for row in rows:
            for k, v in row.items():
                if isinstance(v, list):
                    row[k] = ", ".join(str(i) for i in v)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Saved {len(rows)} records to {filepath}")


# ─────────────────────────────────────────────
#  SECTION 4: HTML/XML Parsing Utilities
# ─────────────────────────────────────────────

class HTMLParser:
    """Utility class for common HTML/XML parsing tasks."""

    @staticmethod
    def extract_table(soup: BeautifulSoup, table_index: int = 0) -> List[dict]:
        """Extract an HTML table into a list of dicts."""
        tables = soup.find_all("table")
        if table_index >= len(tables):
            return []
        table = tables[table_index]
        headers = [th.get_text(strip=True) for th in table.select("thead th, tr:first-child th")]
        rows = []
        for tr in table.select("tbody tr, tr:not(:first-child)"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if headers and len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        return rows

    @staticmethod
    def parse_xml(xml_content: str) -> BeautifulSoup:
        """Parse XML content with BeautifulSoup's lxml-xml parser."""
        return BeautifulSoup(xml_content, "xml")

    @staticmethod
    def extract_metadata(soup: BeautifulSoup) -> dict:
        """Extract Open Graph and meta tags from a page."""
        meta = {}
        for tag in soup.find_all("meta"):
            name  = tag.get("name") or tag.get("property", "")
            content = tag.get("content", "")
            if name and content:
                meta[name] = content
        return meta


# ─────────────────────────────────────────────
#  SECTION 5: Main — Demo Usage
# ─────────────────────────────────────────────

def demo_beautifulsoup():
    """Demo: scrape quotes from quotes.toscrape.com (a safe test site)."""
    TARGET = "https://quotes.toscrape.com"
    logger.info(f"=== BeautifulSoup Demo: {TARGET} ===")

    scraper = BeautifulSoupScraper(base_url=TARGET, delay=0.5)
    soup = scraper.fetch_page(TARGET)
    if not soup:
        logger.error("Could not fetch the demo page.")
        return

    quotes = []
    for block in soup.select(".quote"):
        quotes.append({
            "text":   block.select_one(".text").get_text(strip=True),
            "author": block.select_one(".author").get_text(strip=True),
            "tags":   [t.get_text() for t in block.select(".tag")],
        })

    logger.info(f"Extracted {len(quotes)} quotes.")
    DataExporter.to_json(quotes, "quotes_output.json")
    DataExporter.to_csv(quotes, "quotes_output.csv")
    return quotes


def demo_scrapy():
    """Demo: run the Scrapy spider (requires scrapy installed)."""
    if not SCRAPY_AVAILABLE:
        logger.warning("Scrapy is not installed. Run: pip install scrapy")
        return
    process = CrawlerProcess()
    process.crawl(ArticleSpider)
    process.start()


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "bs4"

    if mode == "scrapy":
        demo_scrapy()
    else:
        results = demo_beautifulsoup()
        if results:
            print("\n── Sample Output (first 3 quotes) ──")
            for q in results[:3]:
                print(f'  "{q["text"][:60]}…"  — {q["author"]}')