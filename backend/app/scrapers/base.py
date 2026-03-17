from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
import random
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProperty:
    name: str
    price: int  # yen
    management_fee: int | None = None
    deposit: str | None = None
    key_money: str | None = None
    address: str | None = None
    layout: str | None = None
    area: str | None = None
    floor: str | None = None
    age: str | None = None
    access: str | None = None
    detail_url: str | None = None
    external_id: str | None = None


class BaseScraper(ABC):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    def fetch_page(self, url: str) -> BeautifulSoup:
        time.sleep(random.uniform(1.0, 3.0))
        response = requests.get(url, headers=self.HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return BeautifulSoup(response.text, "lxml")

    @abstractmethod
    def scrape_property(self, url: str) -> list[ScrapedProperty]:
        """Scrape a single property page."""
        pass

    @abstractmethod
    def scrape_search(self, url: str) -> list[ScrapedProperty]:
        """Scrape a search results page."""
        pass
