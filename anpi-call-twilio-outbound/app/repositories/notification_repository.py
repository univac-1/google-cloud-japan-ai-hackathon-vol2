"""異常時の通知を送信するリポジトリの抽象インターフェース"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from analysis.detect_anomaly import AnomalyResult


class NotificationRepository(ABC):
    """異常時の通知を送信するリポジトリの抽象クラス"""
    
    @abstractmethod
    async def send_anomaly_notification(self, user_id: str, result: AnomalyResult) -> Dict[str, Any]:
        """
        異常検知時の通知を送信
        
        Args:
            user_id: ユーザーID
            result: 異常検知結果
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        pass