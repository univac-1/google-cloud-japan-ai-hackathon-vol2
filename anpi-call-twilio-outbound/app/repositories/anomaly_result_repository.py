"""異常検知結果を保存するリポジトリの抽象インターフェース"""

from abc import ABC, abstractmethod
from analysis.detect_anomaly import AnomalyResult


class AnomalyResultRepository(ABC):
    """異常検知結果を保存するリポジトリの抽象クラス"""
    
    @abstractmethod
    async def save_result(self, user_id: str, result: AnomalyResult) -> str:
        """
        異常検知結果を保存
        
        Args:
            user_id: ユーザーID
            result: 異常検知結果
            
        Returns:
            str: 保存されたレコードのID
        """
        pass