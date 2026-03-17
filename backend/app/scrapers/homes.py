import re
import logging
from urllib.parse import urljoin
from .base import BaseScraper, ScrapedProperty

logger = logging.getLogger(__name__)

BASE_URL = "https://www.homes.co.jp"


def parse_price(text: str) -> int | None:
    """Parse price text like '8.5万円' to integer yen (85000)."""
    text = text.strip().replace(",", "").replace("\u3000", "")
    match = re.search(r"([\d.]+)\s*万円", text)
    if match:
        return int(float(match.group(1)) * 10000)
    match = re.search(r"([\d,]+)\s*円", text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


class HomesScraper(BaseScraper):
    def scrape_property(self, url: str) -> list[ScrapedProperty]:
        """Scrape a single HOME'S property detail page."""
        try:
            soup = self.fetch_page(url)
            properties = []

            name_el = soup.select_one("h1.bukkenHead--title, h1.heading--b1")
            name = name_el.get_text(strip=True) if name_el else "不明"

            price = None
            management_fee = None
            deposit = None
            key_money = None
            address = None
            layout = None
            area = None
            floor = None
            age = None
            access = None

            # Try detail table parsing
            detail_items = soup.select(".bukkenSpec dl, .definitionList dt, .prg-bukkenSpec dt")
            current_label = None
            for el in detail_items:
                if el.name == "dt":
                    current_label = el.get_text(strip=True)
                elif el.name == "dd" and current_label:
                    value = el.get_text(strip=True)
                    if "賃料" in current_label:
                        price = parse_price(value)
                    elif "管理費" in current_label or "共益費" in current_label:
                        management_fee = parse_price(value)
                    elif "敷金" in current_label:
                        deposit = value
                    elif "礼金" in current_label:
                        key_money = value
                    elif "所在地" in current_label or "住所" in current_label:
                        address = value
                    elif "間取り" in current_label:
                        layout = value
                    elif "面積" in current_label:
                        area = value
                    elif "階" in current_label:
                        floor = value
                    elif "築年" in current_label:
                        age = value
                    elif "交通" in current_label or "アクセス" in current_label:
                        access = value
                    current_label = None

            # Fallback: try table rows
            if not price:
                for tr in soup.select("table tr, .mod-mergedTable tr"):
                    th = tr.select_one("th")
                    td = tr.select_one("td")
                    if not th or not td:
                        continue
                    label = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if "賃料" in label and not price:
                        price = parse_price(value)
                    elif ("管理費" in label or "共益費" in label) and not management_fee:
                        management_fee = parse_price(value)
                    elif "敷金" in label and not deposit:
                        deposit = value
                    elif "礼金" in label and not key_money:
                        key_money = value
                    elif ("所在地" in label or "住所" in label) and not address:
                        address = value
                    elif "間取り" in label and not layout:
                        layout = value
                    elif "面積" in label and not area:
                        area = value
                    elif ("階" == label or "所在階" in label) and not floor:
                        floor = value
                    elif "築年" in label and not age:
                        age = value

            if price:
                properties.append(ScrapedProperty(
                    name=name, price=price, management_fee=management_fee,
                    deposit=deposit, key_money=key_money, address=address,
                    layout=layout, area=area, floor=floor, age=age,
                    access=access, detail_url=url,
                ))

            return properties
        except Exception as e:
            logger.error(f"Error scraping HOME'S property {url}: {e}")
            return []

    def scrape_search(self, url: str) -> list[ScrapedProperty]:
        """Scrape HOME'S search results page(s)."""
        properties = []
        current_url = url

        try:
            for page_num in range(1, 11):  # max 10 pages
                soup = self.fetch_page(current_url)

                items = soup.select(".mod-bukkenDetail, .prg-cassetteItem, [data-bukken-id]")
                if not items:
                    items = soup.select(".bukkenList--item, .rental-list-item")
                if not items:
                    break

                for item in items:
                    try:
                        prop = self._parse_search_item(item)
                        if prop:
                            properties.append(prop)
                    except Exception as e:
                        logger.warning(f"Error parsing HOME'S search item: {e}")
                        continue

                next_link = soup.select_one("a.next, .pagination a[rel='next'], .mod-pagination--next a")
                if not next_link:
                    break
                next_href = next_link.get("href")
                if not next_href:
                    break
                current_url = urljoin(BASE_URL, next_href)

        except Exception as e:
            logger.error(f"Error scraping HOME'S search {url}: {e}")

        return properties

    def _parse_search_item(self, item) -> ScrapedProperty | None:
        """Parse a single search result item."""
        name_el = item.select_one(".bukkenTitle, .prg-bukkenTitle, h2 a, .bukkenName")
        name = name_el.get_text(strip=True) if name_el else "不明"

        price_el = item.select_one(".bukkenPrice, .prg-bukkenPrice, .price")
        if not price_el:
            return None
        price = parse_price(price_el.get_text(strip=True))
        if not price:
            return None

        address_el = item.select_one(".bukkenAddress, .prg-bukkenAddress, .address")
        address = address_el.get_text(strip=True) if address_el else None

        layout_el = item.select_one(".bukkenMadori, .prg-bukkenMadori, .layout")
        layout = layout_el.get_text(strip=True) if layout_el else None

        area_el = item.select_one(".bukkenMenseki, .prg-bukkenMenseki, .area")
        area = area_el.get_text(strip=True) if area_el else None

        access_el = item.select_one(".bukkenAccess, .prg-bukkenAccess, .access")
        access = access_el.get_text(strip=True) if access_el else None

        age_el = item.select_one(".bukkenAge, .prg-bukkenAge")
        age = age_el.get_text(strip=True) if age_el else None

        detail_link = item.select_one("a[href*='/chintai/']")
        detail_url = urljoin(BASE_URL, detail_link["href"]) if detail_link and detail_link.get("href") else None

        return ScrapedProperty(
            name=name, price=price, address=address, layout=layout,
            area=area, access=access, age=age, detail_url=detail_url,
        )
