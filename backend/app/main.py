import json
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy import inspect, text

from .database import Base, engine, get_db, SessionLocal
from .models import Monitor, Property, PriceRecord, SiteType, MonitorType
from .schemas import MonitorCreate, MonitorUpdate, MonitorOut, PropertyOut, PriceRecordOut, DashboardStats, ScrapeResult, PropertyStatusUpdate
from .service import scrape_monitor, scrape_all_active
from .url_parser import extract_tags

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scrape():
    """Background job to scrape all active monitors."""
    logger.info("Starting scheduled scrape...")
    db = SessionLocal()
    try:
        results = scrape_all_active(db)
        logger.info(f"Scheduled scrape complete: {len(results)} monitors processed")
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")
    finally:
        db.close()


def _run_migrations():
    """Add missing columns to existing tables (lightweight migration)."""
    inspector = inspect(engine)

    # Define expected columns per table: (table, column, sql_type, default)
    expected_columns = [
        ("monitors", "tags", "TEXT", None),
        ("monitors", "is_active", "INTEGER", "1"),
        ("monitors", "updated_at", "DATETIME", None),
        ("properties", "external_id", "VARCHAR", None),
        ("properties", "is_listed", "INTEGER", "1"),
        ("properties", "last_seen", "DATETIME", None),
        ("properties", "first_seen", "DATETIME", None),
        ("properties", "access", "VARCHAR", None),
        ("properties", "age", "VARCHAR", None),
        ("properties", "floor", "VARCHAR", None),
        ("properties", "area", "VARCHAR", None),
        ("properties", "layout", "VARCHAR", None),
        ("properties", "address", "VARCHAR", None),
        ("properties", "detail_url", "TEXT", None),
        ("properties", "user_status", "VARCHAR", None),
        ("price_records", "management_fee", "INTEGER", None),
        ("price_records", "deposit", "VARCHAR", None),
        ("price_records", "key_money", "VARCHAR", None),
    ]

    with engine.connect() as conn:
        table_columns = {}
        for table, column, sql_type, default in expected_columns:
            if table not in table_columns:
                if table in inspector.get_table_names():
                    table_columns[table] = {c["name"] for c in inspector.get_columns(table)}
                else:
                    table_columns[table] = set()
            if table in table_columns and column not in table_columns[table]:
                default_clause = f" DEFAULT {default}" if default is not None else ""
                logger.info(f"Adding missing column '{column}' to table '{table}'")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}{default_clause}"))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _run_migrations()

    interval_hours = int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))
    scheduler.add_job(scheduled_scrape, "interval", hours=interval_hours, id="scrape_job")
    scheduler.start()
    logger.info(f"Scheduler started: scraping every {interval_hours} hours")

    yield

    scheduler.shutdown()


app = FastAPI(title="RentWatch API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _monitor_tags(monitor: Monitor) -> list[str]:
    """Get tags from DB or empty list."""
    if monitor.tags:
        try:
            return json.loads(monitor.tags)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _monitor_to_out(monitor: Monitor, db: Session) -> MonitorOut:
    prop_count = db.query(func.count(Property.id)).filter(Property.monitor_id == monitor.id).scalar()
    return MonitorOut(
        id=monitor.id, name=monitor.name, site=monitor.site.value,
        monitor_type=monitor.monitor_type.value, url=monitor.url,
        tags=_monitor_tags(monitor),
        is_active=bool(monitor.is_active), created_at=monitor.created_at,
        updated_at=monitor.updated_at, property_count=prop_count,
    )


def _run_initial_scrape(monitor_id: int):
    """Run scrape in background after monitor creation."""
    db = SessionLocal()
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if monitor:
            result = scrape_monitor(db, monitor)
            logger.info(f"Initial scrape for '{monitor.name}': {result}")
    except Exception as e:
        logger.error(f"Initial scrape failed for monitor {monitor_id}: {e}")
    finally:
        db.close()


# ── Dashboard ──────────────────────────────────────────────

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    total_monitors = db.query(func.count(Monitor.id)).scalar()
    active_monitors = db.query(func.count(Monitor.id)).filter(Monitor.is_active == 1).scalar()
    total_properties = db.query(func.count(Property.id)).scalar()
    total_listed = db.query(func.count(Property.id)).filter(Property.is_listed == 1).scalar()
    delisted = total_properties - total_listed

    last_record = db.query(PriceRecord).order_by(PriceRecord.recorded_at.desc()).first()
    last_scan = last_record.recorded_at if last_record else None

    price_drops = 0
    price_increases = 0

    properties_with_records = db.query(Property).all()
    for prop in properties_with_records:
        records = db.query(PriceRecord).filter(
            PriceRecord.property_id == prop.id
        ).order_by(PriceRecord.recorded_at.desc()).limit(2).all()
        if len(records) >= 2:
            diff = records[0].price - records[1].price
            if diff < 0:
                price_drops += 1
            elif diff > 0:
                price_increases += 1

    return DashboardStats(
        total_monitors=total_monitors,
        active_monitors=active_monitors,
        total_properties=total_properties,
        total_listed=total_listed,
        delisted=delisted,
        price_drops=price_drops,
        price_increases=price_increases,
        last_scan=last_scan,
    )


# ── Monitors ──────────────────────────────────────────────

@app.get("/api/monitors", response_model=list[MonitorOut])
def list_monitors(db: Session = Depends(get_db)):
    monitors = db.query(Monitor).order_by(Monitor.created_at.desc()).all()
    return [_monitor_to_out(m, db) for m in monitors]


@app.post("/api/monitors", response_model=MonitorOut)
def create_monitor(data: MonitorCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Auto-extract tags from URL
    tags = extract_tags(data.url, data.site)

    monitor = Monitor(
        name=data.name,
        site=SiteType(data.site),
        monitor_type=MonitorType(data.monitor_type),
        url=data.url,
        tags=json.dumps(tags, ensure_ascii=False) if tags else None,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    # Auto-scrape on creation
    background_tasks.add_task(_run_initial_scrape, monitor.id)

    return _monitor_to_out(monitor, db)


@app.patch("/api/monitors/{monitor_id}", response_model=MonitorOut)
def update_monitor(monitor_id: int, data: MonitorUpdate, db: Session = Depends(get_db)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    if data.name is not None:
        monitor.name = data.name
    if data.is_active is not None:
        monitor.is_active = 1 if data.is_active else 0
    db.commit()
    db.refresh(monitor)
    return _monitor_to_out(monitor, db)


@app.delete("/api/monitors/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    db.delete(monitor)
    db.commit()
    return {"ok": True}


# ── Scraping ──────────────────────────────────────────────

@app.post("/api/monitors/{monitor_id}/scrape", response_model=ScrapeResult)
def trigger_scrape(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    result = scrape_monitor(db, monitor)
    return ScrapeResult(**result)


@app.post("/api/scrape-all")
def trigger_scrape_all(db: Session = Depends(get_db)):
    results = scrape_all_active(db)
    return {"results": results}


# ── Properties ──────────────────────────────────────────────

@app.get("/api/monitors/{monitor_id}/properties", response_model=list[PropertyOut])
def list_properties(
    monitor_id: int,
    sort: str = "price_asc",
    layout: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    status: str | None = None,  # "listed", "delisted", or None for all
    user_status: str | None = None,  # "favorite", "not_interested", or None for all
    db: Session = Depends(get_db),
):
    query = db.query(Property).filter(Property.monitor_id == monitor_id)

    if status == "listed":
        query = query.filter(Property.is_listed == 1)
    elif status == "delisted":
        query = query.filter(Property.is_listed == 0)

    if user_status == "favorite":
        query = query.filter(Property.user_status == "favorite")
    elif user_status == "not_interested":
        query = query.filter(Property.user_status == "not_interested")
    elif user_status == "unmarked":
        query = query.filter(Property.user_status.is_(None))

    if layout:
        query = query.filter(Property.layout.contains(layout))

    props = query.all()
    results = []

    for p in props:
        records = db.query(PriceRecord).filter(
            PriceRecord.property_id == p.id
        ).order_by(PriceRecord.recorded_at.desc()).all()

        current_price = records[0].price if records else None
        price_change = None
        if len(records) >= 2:
            price_change = records[0].price - records[1].price

        # Apply price filter
        if price_min and current_price and current_price < price_min:
            continue
        if price_max and current_price and current_price > price_max:
            continue

        results.append(PropertyOut(
            id=p.id, monitor_id=p.monitor_id, external_id=p.external_id,
            name=p.name, address=p.address, layout=p.layout, area=p.area,
            floor=p.floor, age=p.age, access=p.access, detail_url=p.detail_url,
            is_listed=bool(p.is_listed), user_status=p.user_status,
            last_seen=p.last_seen, first_seen=p.first_seen,
            price_records=[PriceRecordOut.model_validate(r) for r in records],
            current_price=current_price, price_change=price_change,
        ))

    # Sort
    if sort == "price_asc":
        results.sort(key=lambda x: x.current_price or 0)
    elif sort == "price_desc":
        results.sort(key=lambda x: x.current_price or 0, reverse=True)
    elif sort == "change_asc":
        results.sort(key=lambda x: x.price_change or 0)
    elif sort == "change_desc":
        results.sort(key=lambda x: x.price_change or 0, reverse=True)
    elif sort == "newest":
        results.sort(key=lambda x: x.first_seen, reverse=True)

    return results


@app.get("/api/properties/{property_id}/history", response_model=list[PriceRecordOut])
def get_price_history(property_id: int, db: Session = Depends(get_db)):
    records = db.query(PriceRecord).filter(
        PriceRecord.property_id == property_id
    ).order_by(PriceRecord.recorded_at.asc()).all()
    return [PriceRecordOut.model_validate(r) for r in records]


@app.patch("/api/properties/{property_id}/status")
def update_property_status(property_id: int, data: PropertyStatusUpdate, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if data.user_status is not None and data.user_status not in ("favorite", "not_interested"):
        raise HTTPException(status_code=400, detail="Invalid status. Use 'favorite', 'not_interested', or null")
    prop.user_status = data.user_status
    db.commit()
    return {"ok": True, "user_status": prop.user_status}


# ── Price Changes Feed ──────────────────────────────────────

@app.get("/api/price-changes")
def get_price_changes(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent price changes across all monitors."""
    changes = []
    properties = db.query(Property).all()
    for prop in properties:
        records = db.query(PriceRecord).filter(
            PriceRecord.property_id == prop.id
        ).order_by(PriceRecord.recorded_at.desc()).limit(2).all()

        if len(records) >= 2:
            diff = records[0].price - records[1].price
            if diff != 0:
                changes.append({
                    "property_id": prop.id,
                    "property_name": prop.name,
                    "monitor_id": prop.monitor_id,
                    "old_price": records[1].price,
                    "new_price": records[0].price,
                    "change": diff,
                    "changed_at": records[0].recorded_at.isoformat(),
                    "detail_url": prop.detail_url,
                })

    changes.sort(key=lambda x: x["changed_at"], reverse=True)
    return changes[:limit]
