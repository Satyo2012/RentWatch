from pydantic import BaseModel
from datetime import datetime


class MonitorCreate(BaseModel):
    name: str
    site: str  # "suumo" or "homes"
    monitor_type: str  # "url" or "search"
    url: str


class MonitorUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class PriceRecordOut(BaseModel):
    id: int
    price: int
    management_fee: int | None
    deposit: str | None
    key_money: str | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class PropertyOut(BaseModel):
    id: int
    monitor_id: int
    external_id: str | None
    name: str
    address: str | None
    layout: str | None
    area: str | None
    floor: str | None
    age: str | None
    access: str | None
    detail_url: str | None
    first_seen: datetime
    price_records: list[PriceRecordOut]
    current_price: int | None = None
    price_change: int | None = None

    class Config:
        from_attributes = True


class MonitorOut(BaseModel):
    id: int
    name: str
    site: str
    monitor_type: str
    url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    property_count: int = 0

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_monitors: int
    active_monitors: int
    total_properties: int
    price_drops: int
    price_increases: int
    last_scan: datetime | None


class ScrapeResult(BaseModel):
    monitor_id: int
    properties_found: int
    new_properties: int
    price_changes: int
