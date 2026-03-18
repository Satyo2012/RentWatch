import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from .models import Monitor, Property, PriceRecord, SiteType, MonitorType
from .scrapers.suumo import SuumoScraper
from .scrapers.homes import HomesScraper
from .scrapers.base import ScrapedProperty

logger = logging.getLogger(__name__)


def get_scraper(site: SiteType):
    if site == SiteType.SUUMO:
        return SuumoScraper()
    elif site == SiteType.HOMES:
        return HomesScraper()
    raise ValueError(f"Unknown site: {site}")


def scrape_monitor(db: Session, monitor: Monitor) -> dict:
    """Run scraping for a single monitor and update DB."""
    scraper = get_scraper(monitor.site)

    if monitor.monitor_type == MonitorType.URL:
        scraped = scraper.scrape_property(monitor.url)
    else:
        scraped = scraper.scrape_search(monitor.url)

    new_count = 0
    change_count = 0
    now = datetime.now(timezone.utc)

    # Collect detail_urls/names of currently found properties to detect delisting
    found_keys = set()

    for sp in scraped:
        key = sp.detail_url or f"{sp.name}||{sp.address}"
        found_keys.add(key)

        prop = _find_existing_property(db, monitor.id, sp)
        if prop:
            # Re-list if previously delisted
            if not prop.is_listed:
                prop.is_listed = 1
            prop.last_seen = now
            changed = _update_price(db, prop, sp)
            if changed:
                change_count += 1
        else:
            prop = _create_property(db, monitor.id, sp)
            new_count += 1

    # Detect delisted properties (only for search-type monitors)
    delisted_count = 0
    if monitor.monitor_type == MonitorType.SEARCH and scraped:
        existing_props = db.query(Property).filter(
            Property.monitor_id == monitor.id,
            Property.is_listed == 1,
        ).all()
        for prop in existing_props:
            key = prop.detail_url or f"{prop.name}||{prop.address}"
            if key not in found_keys:
                prop.is_listed = 0
                delisted_count += 1

    db.commit()

    return {
        "monitor_id": monitor.id,
        "properties_found": len(scraped),
        "new_properties": new_count,
        "price_changes": change_count,
        "delisted": delisted_count,
    }


def _find_existing_property(db: Session, monitor_id: int, sp: ScrapedProperty) -> Property | None:
    """Find existing property by URL or name+address combo."""
    if sp.detail_url:
        prop = db.query(Property).filter(
            Property.monitor_id == monitor_id,
            Property.detail_url == sp.detail_url,
        ).first()
        if prop:
            return prop

    return db.query(Property).filter(
        Property.monitor_id == monitor_id,
        Property.name == sp.name,
        Property.address == sp.address,
    ).first()


def _create_property(db: Session, monitor_id: int, sp: ScrapedProperty) -> Property:
    """Create new property with initial price record."""
    prop = Property(
        monitor_id=monitor_id,
        external_id=sp.external_id,
        name=sp.name,
        address=sp.address,
        layout=sp.layout,
        area=sp.area,
        floor=sp.floor,
        age=sp.age,
        access=sp.access,
        detail_url=sp.detail_url,
    )
    db.add(prop)
    db.flush()

    record = PriceRecord(
        property_id=prop.id,
        price=sp.price,
        management_fee=sp.management_fee,
        deposit=sp.deposit,
        key_money=sp.key_money,
    )
    db.add(record)
    return prop


def _update_price(db: Session, prop: Property, sp: ScrapedProperty) -> bool:
    """Check if price changed and add new record if so. Returns True if changed."""
    latest = db.query(PriceRecord).filter(
        PriceRecord.property_id == prop.id,
    ).order_by(PriceRecord.recorded_at.desc()).first()

    if latest and latest.price == sp.price:
        return False

    record = PriceRecord(
        property_id=prop.id,
        price=sp.price,
        management_fee=sp.management_fee,
        deposit=sp.deposit,
        key_money=sp.key_money,
    )
    db.add(record)
    return True


def scrape_all_active(db: Session) -> list[dict]:
    """Scrape all active monitors."""
    monitors = db.query(Monitor).filter(Monitor.is_active == 1).all()
    results = []
    for monitor in monitors:
        try:
            result = scrape_monitor(db, monitor)
            results.append(result)
            logger.info(f"Scraped monitor '{monitor.name}': {result}")
        except Exception as e:
            logger.error(f"Error scraping monitor '{monitor.name}': {e}")
            results.append({
                "monitor_id": monitor.id,
                "properties_found": 0,
                "new_properties": 0,
                "price_changes": 0,
                "delisted": 0,
                "error": str(e),
            })
    return results
