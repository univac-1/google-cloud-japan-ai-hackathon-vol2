"""文字起こしデータのモデル定義"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionMessage(BaseModel):
    """個別の文字起こしメッセージ"""
    speaker: str = Field(..., description="話者 ('user' または 'assistant')")
    text: str = Field(..., description="文字起こしテキスト")
    timestamp: datetime = Field(..., description="タイムスタンプ")
    call_sid: str = Field(..., description="通話セッションID")
    user_id: Optional[str] = Field(None, description="ユーザーID（assistantの場合はNone）")