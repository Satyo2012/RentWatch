import re
import logging
from urllib.parse import urljoin
from .base import BaseScraper, ScrapedProperty

logger = logging.getLogger(__name__)

BASE_URL = "https://suumo.jp"


def parse_price(text: str) -> int | None:
    """Parse price text like '8.5万円' to integer yen (85000)."""
    text = text.strip().replace(",", "")
    match = re.search(r"([\d.]+)\s*万円", text)
    if match:
        return int(float(match.group(1)) * 10000)
    match = re.search(r"([\d,]+)\s*円", text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


class SuumoScraper(BaseScraper):
    def scrape_property(self, url: str) -> list[ScrapedProperty]:
        """Scrape a single SUUMO property detail page."""
        try:
            soup = self.fetch_page(url)
            properties = []

            name_el = soup.select_one(".section_h1-header-title")
            name = name_el.get_text(strip=True) if name_el else "不明"

            tables = soup.select("table.data_table")
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

            for table in tables:
                rows = table.select("tr")
                for row in rows:
                    th = row.select_one("th")
                    td = row.select_one("td")
                    if not th or not td:
                        continue
                    label = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if "賃料" in label:
                        price = parse_price(value)
                    elif "管理費" in label or "共益費" in label:
                        management_fee = parse_price(value)
                    elif "敷金" in label:
                        deposit = value
                    elif "礼金" in label:
                        key_money = value
                    elif "所在地" in label or "住所" in label:
                        address = value
                    elif "間取り" in label:
                        layout = value
                    elif "専有面積" in label or "面積" in label:
                        area = value
                    elif "階" == label or "所在階" in label:
                        floor = value
                    elif "築年" in label:
                        age = value

            access_el = soup.select_one(".data_table--traffic")
            if access_el:
                access = access_el.get_text(strip=True)

            if price:
                properties.append(ScrapedProperty(
                    name=name, price=price, management_fee=management_fee,
                    deposit=deposit, key_money=key_money, address=address,
                    layout=layout, area=area, floor=floor, age=age,
                    access=access, detail_url=url,
                ))

            return properties
        except Exception as e:
            logger.error(f"Error scraping SUUMO property {url}: {e}")
            return []

    def scrape_search(self, url: str) -> list[ScrapedProperty]:
        """Scrape SUUMO search results page(s)."""
        properties = []
        current_url = url

        try:
            for page_num in range(1, 11):  # max 10 pages
                soup = self.fetch_page(current_url)
                items = soup.select(".cassetteitem")

                if not items:
                    break

                for item in items:
                    try:
                        props = self._parse_search_item(item)
                        properties.extend(props)
                    except Exception as e:
                        logger.warning(f"Error parsing SUUMO search item: {e}")
                        continue

                next_link = soup.select_one(".pagination-parts a[rel='next']")
                if not next_link:
                    break
                next_href = next_link.get("href")
                if not next_href:
                    break
                current_url = urljoin(BASE_URL, next_href)

        except Exception as e:
            logger.error(f"Error scraping SUUMO search {url}: {e}")

        return properties

    def _parse_search_item(self, item) -> list[ScrapedProperty]:
        """Parse a single search result cassette item (may contain multiple rooms)."""
        results = []

        building_name_el = item.select_one(".cassetteitem_content-title")
        building_name = building_name_el.get_text(strip=True) if building_name_el else "不明"

        address_el = item.select_one(".cassetteitem_detail-col1")
        address = address_el.get_text(strip=True) if address_el else None

        access_parts = item.select(".cassetteitem_detail-col2 .cassetteitem_detail-text")
        access = " / ".join(p.get_text(strip=True) for p in access_parts) if access_parts else None

        age_area = item.select(".cassetteitem_detail-col3 div")
        age = age_area[0].get_text(strip=True) if len(age_area) > 0 else None

        rooms = item.select("table.cassetteitem_other tbody")
        for room in rooms:
            tds = room.select("td")
            if len(tds) < 6:
                continue

            floor = tds[2].get_text(strip=True) if len(tds) > 2 else None
            price_text = tds[3].select_one(".cassetteitem_other-emphasis")
            price = parse_price(price_text.get_text(strip=True)) if price_text else None
            if not price:
                continue

            mgmt_el = tds[3].select_one(".cassetteitem_price--administration")
            management_fee = parse_price(mgmt_el.get_text(strip=True)) if mgmt_el else None

            deposit_el = tds[3].select_one(".cassetteitem_price--deposit")
            deposit = deposit_el.get_text(strip=True) if deposit_el else None

            key_money_el = tds[3].select_one(".cassetteitem_price--gratuity")
            key_money = key_money_el.get_text(strip=True) if key_money_el else None

            layout_el = tds[4].select_one(".cassetteitem_madori")
            layout = layout_el.get_text(strip=True) if layout_el else None

            area_el = tds[4].select_one(".cassetteitem_menseki")
            area_val = area_el.get_text(strip=True) if area_el else None

            detail_link = tds[8].select_one("a") if len(tds) > 8 else None
            detail_url = urljoin(BASE_URL, detail_link["href"]) if detail_link and detail_link.get("href") else None

            room_name = building_name
            floor_text = f" {floor}" if floor else ""
            room_name = f"{building_name}{floor_text}"

            results.append(ScrapedProperty(
                name=room_name, price=price, management_fee=management_fee,
                deposit=deposit, key_money=key_money, address=address,
                layout=layout, area=area_val, floor=floor, age=age,
                access=access, detail_url=detail_url,
            ))

        return results
