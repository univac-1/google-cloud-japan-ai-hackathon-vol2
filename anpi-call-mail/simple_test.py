#!/usr/bin/env python3
"""
シンプルなメール送信テスト
SendGrid APIを直接使用してメールを送信
"""

import os
import time
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# .envファイルを読み込み
load_dotenv()

def simple_email_test():
    """シンプルなメール送信テスト"""
    
    # 環境変数から設定値を取得
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')
    from_name = os.getenv('FROM_NAME', 'AnpiCall安否確認システム')
    to_name = os.getenv('TO_NAME', 'テストユーザー')
    
    # 必要な環境変数がない場合はエラー
    if not api_key:
        print("❌ SENDGRID_API_KEYが設定されていません")
        return False
    if not from_email:
        print("❌ FROM_EMAILが設定されていません")
        return False
    if not to_email:
        print("❌ TO_EMAILが設定されていません")
        return False
    
    print("📧 AnpiCall メール送信テスト")
    print("=" * 50)
    print(f"送信元: {from_email}")
    print(f"送信先: {to_email}")
    print("=" * 50)
    
    # メールコンテンツ
    subject = "【AnpiCall】メール送信機能テスト"
    content = f"""
    <html>
    <head><title>AnpiCall テストメール</title></head>
    <body>
        <h2>🚨 AnpiCall 安否確認システムからのテストメール</h2>
        <p>お疲れ様です。</p>
        <p>これはAnpiCall安否確認システムからのテスト送信メールです。</p>
        <p>メール送信機能が正常に動作することを確認しています。</p>
        <hr>
        <p><strong>送信日時:</strong> {time.strftime("%Y年%m月%d日 %H:%M:%S")}</p>
        <p><strong>送信元:</strong> {from_email}</p>
        <p><strong>送信先:</strong> {to_email}</p>
        <p><strong>APIキー（末尾4文字）:</strong> ...{api_key[-4:]}</p>
        <hr>
        <p><small>このメールは自動送信されています。返信の必要はありません。</small></p>
    </body>
    </html>
    """
    
    try:
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
        
        print("🚀 メール送信を実行中...")
        
        # メールを送信
        response = sg.send(mail)
        
        print("✅ メール送信が成功しました!")
        print(f"   ステータスコード: {response.status_code}")
        print(f"   メッセージID: {response.headers.get('X-Message-Id', 'N/A')}")
        print()
        print("📬 メールボックスを確認してください:")
        print(f"   受信者: {to_email}")
        print(f"   件名: {subject}")
        print()
        print("🔍 送信詳細:")
        print(f"   日時: {time.strftime('%Y年%m月%d日 %H:%M:%S')}")
        print(f"   送信者: {from_email} ({from_name})")
        print(f"   受信者: {to_email} ({to_name})")
        print(f"   APIキー（末尾4文字）: ...{api_key[-4:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ メール送信中にエラーが発生しました: {str(e)}")
        return False

def test_sendgrid_api():
    """SendGrid APIの接続テスト"""
    api_key = os.getenv('SENDGRID_API_KEY')
    
    print("🔧 SendGrid API接続テスト")
    print("=" * 30)
    
    if not api_key:
        print("❌ SENDGRID_API_KEYが設定されていません")
        return False
    
    try:
        sg = SendGridAPIClient(api_key)
        print("✅ SendGrid APIクライアントの初期化が完了しました")
        print(f"   APIキー（末尾4文字）: ...{api_key[-4:]}")
        return True
    except Exception as e:
        print(f"❌ SendGrid API接続エラー: {str(e)}")
        return False

if __name__ == '__main__':
    print("📧 AnpiCall メール送信テストツール v2")
    print("=" * 60)
    
    # API接続テスト
    if test_sendgrid_api():
        print()
        # メール送信テスト
        if simple_email_test():
            print("🎉 全てのテストが成功しました!")
        else:
            print("💥 メール送信テストが失敗しました")
    else:
        print("💥 API接続テストが失敗しました")
