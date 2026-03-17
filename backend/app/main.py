import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler

from .database import Base, engine, get_db, SessionLocal
from .models import Monitor, Property, PriceRecord, SiteType, MonitorType
from .schemas import MonitorCreate, MonitorUpdate, MonitorOut, PropertyOut, PriceRecordOut, DashboardStats, ScrapeResult
from .service import scrape_monitor, scrape_all_active

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

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


# ── Dashboard ──────────────────────────────────────────────

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    total_monitors = db.query(func.count(Monitor.id)).scalar()
    active_monitors = db.query(func.count(Monitor.id)).filter(Monitor.is_active == 1).scalar()
    total_properties = db.query(func.count(Property.id)).scalar()

    last_record = db.query(PriceRecord).order_by(PriceRecord.recorded_at.desc()).first()
    last_scan = last_record.recorded_at if last_record else None

    # Count properties with price changes
    from sqlalchemy import text
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
        price_drops=price_drops,
        price_increases=price_increases,
        last_scan=last_scan,
    )


# ── Monitors ──────────────────────────────────────────────

@app.get("/api/monitors", response_model=list[MonitorOut])
def list_monitors(db: Session = Depends(get_db)):
    monitors = db.query(Monitor).order_by(Monitor.created_at.desc()).all()
    results = []
    for m in monitors:
        prop_count = db.query(func.count(Property.id)).filter(Property.monitor_id == m.id).scalar()
        results.append(MonitorOut(
            id=m.id, name=m.name, site=m.site.value, monitor_type=m.monitor_type.value,
            url=m.url, is_active=bool(m.is_active), created_at=m.created_at,
            updated_at=m.updated_at, property_count=prop_count,
        ))
    return results


@app.post("/api/monitors", response_model=MonitorOut)
def create_monitor(data: MonitorCreate, db: Session = Depends(get_db)):
    monitor = Monitor(
        name=data.name,
        site=SiteType(data.site),
        monitor_type=MonitorType(data.monitor_type),
        url=data.url,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return MonitorOut(
        id=monitor.id, name=monitor.name, site=monitor.site.value,
        monitor_type=monitor.monitor_type.value, url=monitor.url,
        is_active=bool(monitor.is_active), created_at=monitor.created_at,
        updated_at=monitor.updated_at, property_count=0,
    )


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
    prop_count = db.query(func.count(Property.id)).filter(Property.monitor_id == monitor.id).scalar()
    return MonitorOut(
        id=monitor.id, name=monitor.name, site=monitor.site.value,
        monitor_type=monitor.monitor_type.value, url=monitor.url,
        is_active=bool(monitor.is_active), created_at=monitor.created_at,
        updated_at=monitor.updated_at, property_count=prop_count,
    )


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
def list_properties(monitor_id: int, db: Session = Depends(get_db)):
    props = db.query(Property).filter(Property.monitor_id == monitor_id).all()
    results = []
    for p in props:
        records = db.query(PriceRecord).filter(
            PriceRecord.property_id == p.id
        ).order_by(PriceRecord.recorded_at.desc()).all()

        current_price = records[0].price if records else None
        price_change = None
        if len(records) >= 2:
            price_change = records[0].price - records[1].price

        results.append(PropertyOut(
            id=p.id, monitor_id=p.monitor_id, external_id=p.external_id,
            name=p.name, address=p.address, layout=p.layout, area=p.area,
            floor=p.floor, age=p.age, access=p.access, detail_url=p.detail_url,
            first_seen=p.first_seen,
            price_records=[PriceRecordOut.model_validate(r) for r in records],
            current_price=current_price, price_change=price_change,
        ))
    return results


@app.get("/api/properties/{property_id}/history", response_model=list[PriceRecordOut])
def get_price_history(property_id: int, db: Session = Depends(get_db)):
    records = db.query(PriceRecord).filter(
        PriceRecord.property_id == property_id
    ).order_by(PriceRecord.recorded_at.asc()).all()
    return [PriceRecordOut.model_validate(r) for r in records]


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
