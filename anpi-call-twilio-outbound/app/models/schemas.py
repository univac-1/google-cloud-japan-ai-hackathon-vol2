from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, date, time
from enum import Enum
from app.models.client_event_types import ClientEventType


class Gender(str, Enum):
    male = "male"
    female = "female"


class Weekday(str, Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class User(BaseModel):
    user_id: str
    last_name: str
    first_name: str
    last_name_kana: str
    first_name_kana: str
    postal_code: str
    prefecture: str
    address_block: str
    address_building: Optional[str] = None
    phone_number: str
    email: str
    gender: Gender
    birth_date: date
    call_time: time
    call_weekday: Weekday
    created_at: datetime
    updated_at: datetime


class Event(BaseModel):
    event_id: str
    title: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    postal_code: str
    prefecture: str
    address_block: str
    address_building: Optional[str] = None
    contact_name: str
    contact_phone: str
    event_url: str
    created_at: datetime
    updated_at: datetime


class ClientMessage(BaseModel):
    type: ClientEventType
    data: Dict[str, Any] = {}