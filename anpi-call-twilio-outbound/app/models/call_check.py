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
    
    @property
    def level(self) -> int:
        """数値レベルを取得（低いほど軽微、高いほど重要）"""
        level_map = {
            "通常": 1,
            "要観察": 2,
            "異常": 3
        }
        return level_map[self.value]
    
    @classmethod
    def from_level(cls, level: int) -> 'SeverityLevel':
        """数値レベルからSeverityLevelを取得"""
        level_map = {1: cls.NORMAL, 2: cls.OBSERVATION, 3: cls.ABNORMAL}
        return level_map.get(level, cls.ABNORMAL)


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