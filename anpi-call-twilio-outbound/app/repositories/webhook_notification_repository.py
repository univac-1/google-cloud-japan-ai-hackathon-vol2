"""Webhook APIを使用した通知リポジトリの実装"""

import os
import json
import logging
from typing import Dict, Any
import aiohttp
from datetime import datetime

from .notification_repository import NotificationRepository
from analysis.detect_anomaly import AnomalyResult

logger = logging.getLogger(__name__)


class WebhookNotificationRepository(NotificationRepository):
    """Webhook APIを使用した通知リポジトリ"""
    
    def __init__(self, webhook_url: str = None, api_key: str = None, timeout: int = 30):
        """
        Args:
            webhook_url: 通知先WebhookURL（環境変数NOTIFICATION_WEBHOOK_URLからも取得可能）
            api_key: API認証キー（環境変数NOTIFICATION_API_KEYからも取得可能）
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.webhook_url = webhook_url or os.getenv("NOTIFICATION_WEBHOOK_URL")
        self.api_key = api_key or os.getenv("NOTIFICATION_API_KEY")
        self.timeout = timeout
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def send_anomaly_notification(self, user_id: str, result: AnomalyResult) -> Dict[str, Any]:
        """
        異常検知時の通知をWebhook APIに送信
        
        Args:
            user_id: ユーザーID
            result: 異常検知結果
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        if not self.webhook_url:
            self.logger.warning("Webhook URLが設定されていません")
            return {
                "success": False,
                "error": "Webhook URLが設定されていません"
            }
        
        try:
            # 送信データを準備
            payload = {
                "event_type": "anomaly_detected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "anomaly_result": {
                    "has_anomaly": result.has_anomaly,
                    "reason": result.reason,
                    "confidence": result.confidence,
                    "detected_issues": result.detected_issues,
                    "source_files": result.source_files
                }
            }
            
            # ヘッダーを準備
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "anpi-call-system/1.0"
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-API-Key"] = self.api_key
            
            # Webhook APIに送信
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        self.logger.info(f"異常通知送信成功: user_id={user_id}, webhook_url={self.webhook_url}")
                        return {
                            "success": True,
                            "status_code": response.status,
                            "response": response_text
                        }
                    else:
                        self.logger.warning(f"異常通知送信失敗: user_id={user_id}, status={response.status}, response={response_text}")
                        return {
                            "success": False,
                            "status_code": response.status,
                            "response": response_text,
                            "error": f"HTTP {response.status}: {response_text}"
                        }
                        
        except aiohttp.ClientTimeout:
            error_msg = f"Webhook API送信タイムアウト: {self.timeout}秒"
            self.logger.error(f"異常通知タイムアウト: user_id={user_id}, error={error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Webhook API送信エラー: {str(e)}"
            self.logger.error(f"異常通知送信エラー: user_id={user_id}, error={e}", exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }