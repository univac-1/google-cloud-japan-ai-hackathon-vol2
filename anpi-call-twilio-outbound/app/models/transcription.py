"""文字起こしデータのモデル定義"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptionMessage(BaseModel):
    """個別の文字起こしメッセージ"""
    speaker: str = Field(..., description="話者 ('user' または 'assistant')")
    text: str = Field(..., description="文字起こしテキスト")
    timestamp: datetime = Field(..., description="タイムスタンプ")


class TranscriptionData(BaseModel):
    """文字起こしデータ全体"""
    user_id: Optional[str] = Field(None, description="ユーザーID")
    call_started_at: datetime = Field(..., description="通話開始時刻")
    saved_at: datetime = Field(..., description="保存時刻")
    is_final: bool = Field(False, description="最終保存かどうか")
    message_count: int = Field(..., description="メッセージ数")
    transcriptions: List[TranscriptionMessage] = Field(..., description="文字起こしデータのリスト")
    formatted_text: str = Field(..., description="整形されたテキスト")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }