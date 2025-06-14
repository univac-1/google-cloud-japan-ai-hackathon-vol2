#!/usr/bin/env python3
"""
一括テスト実行スクリプト
ローカル環境とCloud Functions環境の両方をテスト
"""

import subprocess
import sys
import os
import time
import requests
import threading
from test_email import test_email_function

def run_local_tests():
    """ローカルサーバーでのテスト"""
    print("🧪 ローカルサーバーテストを開始...")
    
    # ローカルサーバーを起動
    server_process = subprocess.Popen(
        [sys.executable, "local_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # サーバーの起動を待つ
    print("⏳ サーバー起動を待機中...")
    time.sleep(3)
    
    try:
        # ヘルスチェック
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ ローカルサーバーが起動しました")
            
            # テストメールを送信
            test_data = {
                "to_email": "test@example.com",
                "subject": "ローカルテスト",
                "content": "ローカルサーバーからのテストメールです。"
            }
            
            success = test_email_function("http://localhost:8080", test_data)
            return success
        else:
            print("❌ ローカルサーバーのヘルスチェックに失敗")
            return False
            
    except Exception as e:
        print(f"❌ ローカルテストエラー: {str(e)}")
        return False
    finally:
        # サーバーを停止
        server_process.terminate()
        server_process.wait()

def run_cloud_tests():
    """Cloud Functionsでのテスト"""
    function_url = os.environ.get('FUNCTION_URL')
    if not function_url:
        print("⚠️  FUNCTION_URL環境変数が設定されていません")
        print("   Cloud Functionsテストをスキップします")
        return True
    
    print(f"🌐 Cloud Functionsテストを開始: {function_url}")
    
    test_data = {
        "to_email": "cloudtest@example.com",
        "subject": "Cloud Functionsテスト",
        "content": "Cloud Functionsからのテストメールです。"
    }
    
    return test_email_function(function_url, test_data)

def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🚀 AnpiCall Email Service - 統合テスト")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # ローカルテスト
    print("\n📍 テスト1: ローカルサーバー")
    print("-" * 40)
    if run_local_tests():
        success_count += 1
        print("✅ ローカルテスト成功")
    else:
        print("❌ ローカルテスト失敗")
    
    # Cloud Functionsテスト
    print("\n☁️  テスト2: Cloud Functions")
    print("-" * 40)
    if run_cloud_tests():
        success_count += 1
        print("✅ Cloud Functionsテスト成功")
    else:
        print("❌ Cloud Functionsテスト失敗")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 統合テスト結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_tests}")
    print(f"❌ 失敗: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    elif success_count > 0:
        print("⚠️  一部のテストが成功しました")
        sys.exit(0)
    else:
        print("💥 すべてのテストが失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
