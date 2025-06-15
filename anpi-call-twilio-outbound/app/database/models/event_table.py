"""
イベントテーブルORM定義
"""
from sqlalchemy import Column, String, DateTime, Text, CHAR, TIMESTAMP
from .base import Base


class EventTable(Base):
    """イベントテーブルのORM定義"""
    __tablename__ = 'events'

    event_id = Column(CHAR(36), primary_key=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    postal_code = Column(CHAR(8), nullable=True)
    prefecture = Column(String(40), nullable=True)
    address_block = Column(String(100), nullable=True)
    address_building = Column(String(100), nullable=True)
    contact_name = Column(String(120), nullable=True)
    contact_phone = Column(String(14), nullable=True)
    event_url = Column(String(2083), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)