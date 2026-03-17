from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .database import Base


class SiteType(str, enum.Enum):
    SUUMO = "suumo"
    HOMES = "homes"


class MonitorType(str, enum.Enum):
    URL = "url"
    SEARCH = "search"


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    site = Column(SAEnum(SiteType), nullable=False)
    monitor_type = Column(SAEnum(MonitorType), nullable=False)
    url = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    properties = relationship("Property", back_populates="monitor", cascade="all, delete-orphan")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    external_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    layout = Column(String, nullable=True)
    area = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    age = Column(String, nullable=True)
    access = Column(String, nullable=True)
    detail_url = Column(Text, nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    monitor = relationship("Monitor", back_populates="properties")
    price_records = relationship("PriceRecord", back_populates="property", cascade="all, delete-orphan")

    @property
    def latest_price(self):
        if self.price_records:
            return max(self.price_records, key=lambda r: r.recorded_at)
        return None


class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    price = Column(Integer, nullable=False)  # in yen
    management_fee = Column(Integer, nullable=True)  # 管理費 in yen
    deposit = Column(String, nullable=True)  # 敷金
    key_money = Column(String, nullable=True)  # 礼金
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    property = relationship("Property", back_populates="price_records")
