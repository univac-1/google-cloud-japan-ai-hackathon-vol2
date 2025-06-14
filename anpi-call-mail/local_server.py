#!/usr/bin/env python3
"""
ローカル開発・テスト用のサーバー
Cloud Functions環境をローカルで再現
"""

import os
from flask import Flask, request
from main import send_email

# Flask アプリケーションを作成
app = Flask(__name__)

# 環境変数の設定（ローカル開発用）
os.environ.setdefault('SENDGRID_API_KEY', 'dummy-api-key-for-local-testing')
os.environ.setdefault('DEFAULT_FROM_EMAIL', 'noreply@localhost.com')
os.environ.setdefault('DEFAULT_FROM_NAME', 'Local Test System')

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def email_endpoint():
    """メール送信エンドポイント"""
    if request.method == 'GET':
        return {
            'message': 'AnpiCall Email Service',
            'status': 'running',
            'endpoints': {
                'send_email': 'POST /',
                'health': 'GET /health'
            }
        }
    return send_email(request)

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェックエンドポイント"""
    return {
        'status': 'healthy',
        'service': 'anpicall-email-local',
        'version': '1.0.0'
    }

if __name__ == '__main__':
    print("🚀 AnpiCall Email Service (Local Development)")
    print("   URL: http://localhost:8080")
    print("   Endpoints:")
    print("     POST /     - メール送信")
    print("     GET /      - サービス情報")
    print("     GET /health - ヘルスチェック")
    print("")
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
