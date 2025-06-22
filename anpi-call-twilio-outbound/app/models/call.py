"""通話データのモデル定義"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.transcription import TranscriptionMessage


class Call(BaseModel):
    """通話データ"""
    call_id: str = Field(..., description="通話ID (Twilio Call SID)")
    user_id: str = Field(..., description="ユーザーID")
    call_started_at: datetime = Field(..., description="通話開始時刻")
    call_ended_at: Optional[datetime] = Field(None, description="通話終了時刻")
    transcriptions: List[TranscriptionMessage] = Field(default_factory=list, description="発言記録リスト")
    
    class Config:
        """Pydantic設定"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }