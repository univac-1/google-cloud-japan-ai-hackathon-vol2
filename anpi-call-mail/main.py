import os
import json
import logging
from flask import Request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(request: Request):
    """
    Cloud Functions HTTPトリガー関数
    SendGrid APIを使用してメールを送信
    
    HTTPリクエスト例:
    POST /
    {
        "to_email": "recipient@example.com",
        "to_name": "受信者名",
        "subject": "件名",
        "content": "メール本文",
        "from_email": "sender@example.com",
        "from_name": "送信者名"
    }
    """
    
    # CORS対応
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    try:
        # SendGrid APIキーを環境変数から取得
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return jsonify({
                'error': 'SendGrid API key not configured',
                'success': False
            }), 500, headers

        # リクエストボディを解析
        if request.content_type == 'application/json':
            request_json = request.get_json(silent=True)
        else:
            return jsonify({
                'error': 'Content-Type must be application/json',
                'success': False
            }), 400, headers

        if not request_json:
            return jsonify({
                'error': 'Invalid JSON payload',
                'success': False
            }), 400, headers

        # 必須パラメータの検証
        required_fields = ['to_email', 'subject', 'content']
        missing_fields = [field for field in required_fields if not request_json.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'success': False
            }), 400, headers

        # メールパラメータを取得
        to_email = request_json['to_email']
        to_name = request_json.get('to_name', to_email)
        subject = request_json['subject']
        content = request_json['content']
        from_email = request_json.get('from_email', os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com'))
        from_name = request_json.get('from_name', os.environ.get('DEFAULT_FROM_NAME', 'System'))

        # メールオブジェクトを作成
        from_email_obj = Email(from_email, from_name)
        to_email_obj = To(to_email, to_name)
        content_obj = Content("text/html", content)
        
        mail = Mail(
            from_email=from_email_obj,
            to_emails=to_email_obj,
            subject=subject,
            html_content=content_obj
        )

        # SendGrid APIクライアントを初期化
        sg = SendGridAPIClient(api_key)
        
        # メールを送信
        response = sg.send(mail)
        
        logger.info(f"Email sent successfully. Status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        return jsonify({
            'message': 'Email sent successfully',
            'success': True,
            'sendgrid_response': {
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id', 'N/A')
            }
        }), 200, headers

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return jsonify({
            'error': f'Failed to send email: {str(e)}',
            'success': False
        }), 500, headers

def health_check(request: Request):
    """
    ヘルスチェック用エンドポイント
    """
    return jsonify({
        'status': 'healthy',
        'service': 'email-sender',
        'version': '1.0.0'
    }), 200
