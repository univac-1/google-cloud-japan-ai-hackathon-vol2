#!/usr/bin/env python3
"""
簡易APIテストスクリプト
"""

import requests
import json

def quick_test():
    print("=== AI Diary API 簡易テスト ===")
    
    # 1. ヘルスチェック
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        print(f"ヘルスチェック: {response.status_code}")
        print(f"レスポンス: {response.json()}")
    except Exception as e:
        print(f"ヘルスチェック失敗: {e}")
        return False
    
    # 2. 実データでのユーザー情報取得テスト
    test_user_id = "04B6A6BD-C767-4618-BEC0-262D7F40F0BD"
    data = {
        "userID": test_user_id,
        "callID": "test-call-001"
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/get-user-info",
            json=data,
            timeout=5
        )
        print(f"\nユーザー情報取得: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ 成功!")
            print(f"ユーザー名: {result['userInfo']['last_name']} {result['userInfo']['first_name']}")
            print(f"電話番号: {result['userInfo'].get('phone_number', 'N/A')}")
            print(f"メール: {result['userInfo'].get('email', 'N/A')}")
            return True
        else:
            print(f"✗ 失敗: {response.text}")
            return False
    except Exception as e:
        print(f"ユーザー情報取得失敗: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n✓ 実データでの情報取得が正常に動作しています！")
    else:
        print("\n✗ テストに失敗しました") 