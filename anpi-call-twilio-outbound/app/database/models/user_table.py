"""
ユーザーテーブルORM定義
"""
from sqlalchemy import Column, String, Date, Time, Enum, CHAR, VARCHAR, TIMESTAMP
from app.models.schemas import Gender, Weekday
from .base import Base


class UserTable(Base):
    """ユーザーテーブルのORM定義"""
    __tablename__ = 'users'

    user_id = Column(CHAR(36), primary_key=True)
    last_name = Column(VARCHAR(64), nullable=False)
    first_name = Column(VARCHAR(64), nullable=False)
    last_name_kana = Column(VARCHAR(64), nullable=True)
    first_name_kana = Column(VARCHAR(64), nullable=True)
    postal_code = Column(CHAR(8), nullable=True)
    prefecture = Column(VARCHAR(40), nullable=True)
    address_block = Column(VARCHAR(100), nullable=True)
    address_building = Column(VARCHAR(100), nullable=True)
    phone_number = Column(VARCHAR(14), nullable=False)
    email = Column(VARCHAR(255), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    birth_date = Column(Date, nullable=True)
    call_time = Column(Time, nullable=True)
    call_weekday = Column(Enum(Weekday), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)