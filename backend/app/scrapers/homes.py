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

            name_el = soup.select_one(
                "h1.bukkenHead--title, h1.heading--b1, "
                "h1[class*='bukken'], h1[class*='Bukken'], "
                ".mod-bukkenHead h1, .property-title h1, h1"
            )
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
        """Scrape HOME'S search results page(s).

        Handles both old and new HOME'S page layouts including
        /chintai/list/ style URLs.
        """
        properties = []
        current_url = url

        try:
            for page_num in range(1, 11):  # max 10 pages
                logger.info(f"Scraping HOME'S search page {page_num}: {current_url}")
                soup = self.fetch_page(current_url)

                # Try multiple selector patterns (old and new layouts)
                items = soup.select(
                    ".mod-bukkenDetail, .prg-cassetteItem, [data-bukken-id], "
                    ".mod-mergedBukken, .mod-bukken, .cassetteitem"
                )
                if not items:
                    items = soup.select(
                        ".bukkenList--item, .rental-list-item, "
                        "[class*='bukken'], [class*='Bukken'], "
                        "article[class*='property'], .p-property-card"
                    )
                if not items:
                    logger.warning(f"No property items found on page {page_num}")
                    break

                logger.info(f"Found {len(items)} items on page {page_num}")

                for item in items:
                    try:
                        prop = self._parse_search_item(item)
                        if prop:
                            properties.append(prop)
                    except Exception as e:
                        logger.warning(f"Error parsing HOME'S search item: {e}")
                        continue

                # Try multiple pagination patterns
                next_link = soup.select_one(
                    "a.next, .pagination a[rel='next'], .mod-pagination--next a, "
                    "a[class*='next'], .pager a[rel='next'], "
                    "nav a[aria-label='次へ'], .paginate_button.next a"
                )
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
        # Property name - try multiple selectors
        name_el = item.select_one(
            ".bukkenTitle, .prg-bukkenTitle, h2 a, .bukkenName, "
            "[class*='bukkenTitle'], [class*='BukkenTitle'], "
            ".cassetteitem_content-title, h3 a"
        )
        name = name_el.get_text(strip=True) if name_el else "不明"

        # Price
        price_el = item.select_one(
            ".bukkenPrice, .prg-bukkenPrice, .price, "
            "[class*='bukkenPrice'], [class*='Price'], "
            ".cassetteitem_price--rent"
        )
        if not price_el:
            return None
        price = parse_price(price_el.get_text(strip=True))
        if not price:
            return None

        # Address
        address_el = item.select_one(
            ".bukkenAddress, .prg-bukkenAddress, .address, "
            "[class*='bukkenAddress'], [class*='Address'], "
            ".cassetteitem_detail-col1"
        )
        address = address_el.get_text(strip=True) if address_el else None

        # Layout
        layout_el = item.select_one(
            ".bukkenMadori, .prg-bukkenMadori, .layout, "
            "[class*='bukkenMadori'], [class*='Madori'], "
            ".cassetteitem_madori"
        )
        layout = layout_el.get_text(strip=True) if layout_el else None

        # Area (floor space)
        area_el = item.select_one(
            ".bukkenMenseki, .prg-bukkenMenseki, .area, "
            "[class*='bukkenMenseki'], [class*='Menseki'], "
            ".cassetteitem_menseki"
        )
        area = area_el.get_text(strip=True) if area_el else None

        # Access (station)
        access_el = item.select_one(
            ".bukkenAccess, .prg-bukkenAccess, .access, "
            "[class*='bukkenAccess'], [class*='Access'], "
            ".cassetteitem_detail-col2"
        )
        access = access_el.get_text(strip=True) if access_el else None

        # Building age
        age_el = item.select_one(
            ".bukkenAge, .prg-bukkenAge, "
            "[class*='bukkenAge'], [class*='Age'], "
            ".cassetteitem_detail-col3"
        )
        age = age_el.get_text(strip=True) if age_el else None

        # Detail link - try broader selectors
        detail_link = item.select_one(
            "a[href*='/chintai/'], a[href*='/detail/'], a[href*='/bukken/']"
        )
        if not detail_link:
            # Fallback: first <a> with an absolute homes.co.jp URL
            detail_link = item.select_one("a[href^='https://www.homes.co.jp']")
        if not detail_link:
            # Fallback: first <a> tag with href
            for a_tag in item.select("a[href]"):
                href = a_tag.get("href", "")
                if href and not href.startswith("#") and not href.startswith("javascript:"):
                    detail_link = a_tag
                    break

        detail_url = urljoin(BASE_URL, detail_link["href"]) if detail_link and detail_link.get("href") else None

        return ScrapedProperty(
            name=name, price=price, address=address, layout=layout,
            area=area, access=access, age=age, detail_url=detail_url,
        )
