"""Email API を使用した通知リポジトリの実装"""

import os
import json
import logging
from typing import Dict, Any
import aiohttp
from datetime import datetime

from .notification_repository import NotificationRepository
from models.call_check import CallCheckResult

logger = logging.getLogger(__name__)


class WebhookNotificationRepository(NotificationRepository):
    """Email API を使用した通知リポジトリ"""

    def __init__(self, email_api_url: str = None, to_email: str = None, timeout: int = 30):
        """
        Args:
            email_api_url: Email API URL（環境変数EMAIL_API_URLからも取得可能）
            to_email: 送信先メールアドレス（環境変数NOTIFICATION_EMAIL_TOからも取得可能）
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.email_api_url = email_api_url or os.getenv("EMAIL_API_URL")
        self.to_email = to_email or os.getenv("NOTIFICATION_EMAIL_TO")
        self.timeout = timeout

    async def send_call_check_notification(self, user_id: str, result: CallCheckResult) -> Dict[str, Any]:
        """
        通話チェック結果の通知をEmail APIに送信

        Args:
            user_id: ユーザーID
            result: 通話チェック結果

        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            # メール件名と本文を生成
            severity_level = result.severity_level
            subject = f"【AnpiCall】通話チェック結果通知 - {severity_level}"

            # 証拠を整理
            evidence_html = ""
            if result.evidence:
                evidence_html = "<h3>判断根拠となる発言:</h3><ul>"
                for ev in result.evidence:
                    speaker_label = "利用者" if ev.speaker == "user" else "オペレーター"
                    evidence_html += f"<li><strong>{speaker_label}:</strong> {ev.statement} <em>(通話ID: {ev.call_id})</em></li>"
                evidence_html += "</ul>"

            # 検出された問題を整理
            issues_html = ""
            if result.detected_issues:
                issues_html = "<h3>検出された問題:</h3><ul>"
                for issue in result.detected_issues:
                    issues_html += f"<li>{issue}</li>"
                issues_html += "</ul>"

            # HTML本文を作成
            content = f"""
            <h1>通話チェック結果通知</h1>
            <p><strong>ユーザーID:</strong> {user_id}</p>
            <p><strong>重要度:</strong> {severity_level}</p>
            <p><strong>分析日時:</strong> {result.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>分析結果</h2>
            <p>{result.reason}</p>
            
            {issues_html}
            {evidence_html}
            
            <h3>分析対象通話:</h3>
            <p>通話数: {len(result.source_calls)}件</p>
            <p>通話ID: {', '.join(result.source_calls)}</p>
            
            <hr>
            <p><em>このメールはAnpiCallシステムから自動送信されています。</em></p>
            """

            # Email API向けのペイロードを準備
            payload = {
                "to_email": self.to_email,
                "subject": subject,
                "content": content
            }

            # ヘッダーを準備
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "anpi-call-system/1.0"
            }

            # Email APIに送信
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    self.email_api_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()

                    if response.status == 200:
                        logger.info(
                            f"通話チェック通知送信成功: user_id={user_id}, severity={severity_level}")
                        return {
                            "success": True,
                            "status_code": response.status,
                            "response": response_text
                        }
                    else:
                        logger.warning(
                            f"通話チェック通知送信失敗: user_id={user_id}, status={response.status}, response={response_text}")
                        return {
                            "success": False,
                            "status_code": response.status,
                            "response": response_text,
                            "error": f"HTTP {response.status}: {response_text}"
                        }

        except aiohttp.ClientTimeout:
            error_msg = f"Email API送信タイムアウト: {self.timeout}秒"
            logger.error(
                f"通話チェック通知タイムアウト: user_id={user_id}, error={error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Email API送信エラー: {str(e)}"
            logger.error(
                f"通話チェック通知送信エラー: user_id={user_id}, error={e}", exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
