"""通話チェック結果のモデル定義"""

from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class SeverityLevel(str, Enum):
    """重要度レベル"""
    NORMAL = "通常"  # 問題なし
    OBSERVATION = "要観察"  # 経過観察が必要
    ABNORMAL = "異常"  # 緊急対応が必要


class Evidence(BaseModel):
    """判断根拠となる発言"""
    call_id: str  # 通話ID
    statement: str  # 発言内容
    speaker: str  # 発言者（user/assistant）


class OpenAICallAnalysisResult(BaseModel):
    """OpenAI通話分析結果"""
    reason: str
    severity_level: SeverityLevel
    detected_issues: List[str]  # 検出された具体的な問題
    evidence: List[Evidence]  # 判断根拠となる発言


class CallCheckResult(BaseModel):
    """通話チェック結果"""
    reason: str
    severity_level: SeverityLevel
    detected_issues: List[str]  # 検出された具体的な問題
    evidence: List[Evidence]  # 判断根拠となる発言
    source_calls: List[str]  # 分析に使用した通話ID
    analyzed_at: datetime  # 分析実行日時