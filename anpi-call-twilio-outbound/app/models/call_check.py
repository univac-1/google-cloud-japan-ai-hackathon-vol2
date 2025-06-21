"""通話チェック結果のモデル定義"""

from typing import List
from pydantic import BaseModel


class OpenAICallAnalysisResult(BaseModel):
    """OpenAI通話分析結果"""
    has_issue: bool
    reason: str
    confidence: float  # 0.0-1.0の信頼度
    detected_issues: List[str]  # 検出された具体的な問題


class CallCheckResult(BaseModel):
    """通話チェック結果"""
    has_issue: bool
    reason: str
    confidence: float  # 0.0-1.0の信頼度
    detected_issues: List[str]  # 検出された具体的な問題
    analyzed_calls: List[str]  # 分析に使用した通話ID
    sources: List[str]  # 判断根拠となった通話ID（analyzed_callsと同じ）