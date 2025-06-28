"""
メール送信サービス

AI日記完成後のメール送信処理を担当
"""

import requests
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def send_diary_email(to_email: str, subject: str, content: str) -> Tuple[bool, str]:
    """
    日記完成メールを送信
    
    Args:
        to_email: 送信先メールアドレス
        subject: 件名
        content: HTMLコンテンツ
        
    Returns:
        Tuple[bool, str]: (成功フラグ, メッセージまたはエラー)
    """
    try:
        email_api_url = "https://send-email-hkzk5xnm7q-an.a.run.app/send_email"
        
        payload = {
            "to_email": to_email,
            "subject": subject,
            "content": content
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(email_api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully to: {to_email}")
            return True, "メール送信成功"
        else:
            error_msg = f"メール送信失敗: HTTP {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "メール送信失敗: タイムアウト"
        logger.error(error_msg)
        return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"メール送信失敗: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"メール送信失敗: 予期しないエラー - {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def process_diary_email_sending(user_info: dict, html_content: str, user_id: str) -> Tuple[bool, str]:
    """
    日記完成メール送信処理
    
    Args:
        user_info: ユーザー情報
        html_content: 送信するHTMLコンテンツ
        user_id: ユーザーID
        
    Returns:
        Tuple[bool, str]: (送信成功フラグ, メッセージ)
    """
    try:
        # ユーザー情報からメールアドレスを取得
        user_email = user_info.get('email')
        
        # ローカル動作確認用の固定メールアドレス
        if user_id == "4CC0CA6A-657C-4253-99FF-C19219D30AE2":
            user_email = "5jpbnd@gmail.com"
        
        # メールアドレスとHTMLコンテンツの検証
        if not user_email:
            message = "ユーザーのメールアドレスが見つかりません"
            logger.warning(f"No email address found for user: {user_id}")
            return False, message
            
        if not html_content:
            message = "HTMLコンテンツが生成されていないためメール送信をスキップしました"
            logger.warning("HTML content is empty, skipping email sending")
            return False, message
        
        # メール送信実行
        email_success, email_msg = send_diary_email(
            to_email=user_email,
            subject="AI日記が完成しました",
            content=html_content
        )
        
        if email_success:
            logger.info(f"Email sent successfully to: {user_email}")
        else:
            logger.warning(f"Email sending failed: {email_msg}")
            
        return email_success, email_msg
        
    except Exception as email_error:
        error_message = f"メール送信エラー: {str(email_error)}"
        logger.error(f"Email sending failed: {str(email_error)}")
        return False, error_message
