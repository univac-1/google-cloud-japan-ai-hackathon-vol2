"""通話チェック結果の通知を送信するリポジトリの抽象インターフェース"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from models.call_check import CallCheckResult


class NotificationRepository(ABC):
    """通話チェック結果の通知を送信するリポジトリの抽象クラス"""
    
    @abstractmethod
    async def send_call_check_notification(self, user_id: str, result: CallCheckResult) -> Dict[str, Any]:
        """
        通話チェック結果の通知を送信
        
        Args:
            user_id: ユーザーID
            result: 通話チェック結果
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        pass