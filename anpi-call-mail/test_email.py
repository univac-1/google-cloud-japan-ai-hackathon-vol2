#!/usr/bin/env python3
"""
メール送信システムのテストスクリプト
Cloud Functions にHTTPリクエストを送信してメール送信をテスト
"""

import requests
import json
import sys
import os

def test_email_function(function_url, test_data):
    """
    Cloud Functions のメール送信をテスト
    
    Args:
        function_url (str): Cloud Functions のURL
        test_data (dict): テスト用のメールデータ
    
    Returns:
        bool: テストが成功したかどうか
    """
    try:
        print(f"🧪 テスト開始: {function_url}")
        print(f"📧 送信データ: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # HTTPリクエストを送信
        response = requests.post(
            function_url, 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 ステータスコード: {response.status_code}")
        print(f"📋 レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ テスト成功: メールが正常に送信されました")
                return True
            else:
                print("❌ テスト失敗: API呼び出しは成功したが、メール送信に失敗")
                return False
        else:
            print(f"❌ テスト失敗: HTTPエラー {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラー: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

def main():
    """メインテスト関数"""
    
    # 環境変数またはコマンドライン引数からFunction URLを取得
    function_url = os.environ.get('FUNCTION_URL')
    if len(sys.argv) > 1:
        function_url = sys.argv[1]
    
    if not function_url:
        print("❌ Cloud Functions のURLが指定されていません")
        print("使用方法:")
        print("  python test_email.py YOUR_FUNCTION_URL")
        print("  または環境変数 FUNCTION_URL を設定してください")
        sys.exit(1)
    
    # テストケース1: 基本的なメール送信
    test_data_1 = {
        "to_email": "test@example.com",
        "to_name": "テストユーザー",
        "subject": "【テスト】AnpiCall メール送信システム",
        "content": """
        <html>
        <head><title>テストメール</title></head>
        <body>
            <h1>🚀 AnpiCall メール送信システム</h1>
            <p>こんにちは、テストユーザー様</p>
            <p>これは <strong>Cloud Functions</strong> + <strong>SendGrid</strong> を使用したテストメールです。</p>
            <ul>
                <li>✅ HTTPトリガー機能</li>
                <li>✅ SendGrid API連携</li>
                <li>✅ HTML形式メール</li>
            </ul>
            <hr>
            <p><small>送信時刻: {timestamp}</small></p>
        </body>
        </html>
        """.format(timestamp=str(requests.utils.default_headers())),
        "from_email": "noreply@anpicall.example.com",
        "from_name": "AnpiCall System"
    }
    
    # テストケース2: 最小限のメール送信
    test_data_2 = {
        "to_email": "minimal@example.com",
        "subject": "最小限テスト",
        "content": "これは最小限のテストメールです。"
    }
    
    print("=" * 60)
    print("🧪 AnpiCall メール送信システム テスト")
    print("=" * 60)
    
    # テスト実行
    success_count = 0
    total_tests = 2
    
    print("\n📧 テストケース1: フル機能テスト")
    print("-" * 40)
    if test_email_function(function_url, test_data_1):
        success_count += 1
    
    print("\n📧 テストケース2: 最小限テスト")
    print("-" * 40)
    if test_email_function(function_url, test_data_2):
        success_count += 1
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_tests}")
    print(f"❌ 失敗: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print("⚠️  一部のテストが失敗しました。")
        sys.exit(1)

if __name__ == "__main__":
    main()
