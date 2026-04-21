"""
==============================================================
  COMPLETE BOOKS SCRAPER — books.toscrape.com
  Features:
    - Scrape all catalogue pages (~1000 books)
    - Extract title, price, rating, URL, image
    - Ratings converted to numbers
    - Saves JSON and CSV (UTF-8)
    - Polite crawling with delays, retry handling
==============================================================
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import logging
import random
from urllib.parse import urljoin
from dataclasses import dataclass, asdict, field
from typing import List
from datetime import datetime

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────
@dataclass
class Book:
    title: str = ""
    url: str = ""
    price: str = ""
    rating: int = 0
    image_url: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

# ─────────────────────────────────────────────
# BOOK SCRAPER
# ─────────────────────────────────────────────
class BookScraper:
    BASE_URL = "https://books.toscrape.com"
    START_URL = f"{BASE_URL}/catalogue/page-1.html"
    ITEM_SELECTOR = "article.product_pod"
    NEXT_PAGE_SELECTOR = "li.next > a"

    RATING_MAP = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        })
        self.visited_urls = set()
        self.books: List[Book] = []

    # ── FETCH PAGE
    def fetch(self, url: str):
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching [{attempt}/{self.max_retries}]: {url}")
                r = self.session.get(url, timeout=10)
                r.raise_for_status()
                return BeautifulSoup(r.text, "html.parser")
            except Exception as e:
                logger.warning(f"Error fetching {url}: {e}")
                time.sleep(self.delay * (2 ** attempt) + random.uniform(0, 0.5))
        logger.error(f"Failed to fetch after {self.max_retries} attempts: {url}")
        return None

    # ── EXTRACT BOOK ITEM
    def extract_book(self, element) -> Book:
        # Title and URL
        title_tag = element.select_one("h3 > a")
        title = title_tag.get("title", "").strip()
        href = title_tag.get("href", "")
        url = urljoin(f"{self.BASE_URL}/catalogue/", href)

        # Price
        price_tag = element.select_one("p.price_color")
        price = price_tag.get_text(strip=True) if price_tag else ""

        # Rating
        rating_tag = element.select_one("p.star-rating")
        rating_classes = rating_tag.get("class", []) if rating_tag else []
        rating_str = next((c for c in rating_classes if c != "star-rating"), "Zero")
        rating = self.RATING_MAP.get(rating_str, 0)

        # Image
        img_tag = element.select_one("div.image_container > a > img")
        img_src = img_tag.get("src", "") if img_tag else ""
        image_url = urljoin(self.BASE_URL, img_src.replace("../../", "/"))

        return Book(title=title, url=url, price=price, rating=rating, image_url=image_url)

    # ── SCRAPE ALL PAGES
    def scrape_all(self):
        url = self.START_URL
        page = 1
        while url:
            if url in self.visited_urls:
                break
            self.visited_urls.add(url)

            logger.info(f"Scraping page {page}: {url}")
            soup = self.fetch(url)
            if not soup:
                break

            for el in soup.select(self.ITEM_SELECTOR):
                book = self.extract_book(el)
                self.books.append(book)

            logger.info(f"Total books so far: {len(self.books)}")

            next_tag = soup.select_one(self.NEXT_PAGE_SELECTOR)
            url = urljoin(self.BASE_URL, next_tag.get("href")) if next_tag else None
            page += 1
            time.sleep(self.delay + random.uniform(0, 0.5))

        logger.info(f"Finished scraping. Total books: {len(self.books)}")
        return self.books

    # ── SAVE JSON
    def save_json(self, filename="books_output.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([asdict(b) for b in self.books], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.books)} books to {filename}")

    # ── SAVE CSV
    def save_csv(self, filename="books_output.csv"):
        if not self.books:
            logger.warning("No data to save")
            return
        fieldnames = list(asdict(self.books[0]).keys())
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for b in self.books:
                writer.writerow(asdict(b))
        logger.info(f"Saved {len(self.books)} books to {filename}")


# ─────────────────────────────────────────────
# RUN SCRAPER
# ─────────────────────────────────────────────
if __name__ == "__main__":
    scraper = BookScraper(delay=1.0)
    all_books = scraper.scrape_all()
    scraper.save_json()
    scraper.save_csv()

    print(f"\n✅ Scraped {len(all_books)} books. Preview:\n")
    for b in all_books[:5]:
        print(f"{b.title} | {b.price} | {b.rating} | {b.url}")