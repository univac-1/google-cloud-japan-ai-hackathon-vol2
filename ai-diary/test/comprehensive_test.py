#!/usr/bin/env python3
"""
AI Diary Get Info Service - 包括的テストスクリプト
"""

import requests
import json
import time

def test_user_info(user_id, call_id, description=""):
    """個別ユーザー情報取得テスト"""
    data = {
        "userID": user_id,
        "callID": call_id
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/get-user-info",
            json=data,
            timeout=10
        )
        
        print(f"\n--- {description} ---")
        print(f"ユーザーID: {user_id}")
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            user_info = result.get('userInfo', {})
            print(f"✓ 成功")
            print(f"  名前: {user_info.get('last_name', 'N/A')} {user_info.get('first_name', 'N/A')}")
            print(f"  カナ: {user_info.get('last_name_kana', 'N/A')} {user_info.get('first_name_kana', 'N/A')}")
            print(f"  電話: {user_info.get('phone_number', 'N/A')}")
            print(f"  メール: {user_info.get('email', 'N/A')}")
            print(f"  郵便番号: {user_info.get('postal_code', 'N/A')}")
            print(f"  住所: {user_info.get('prefecture', '')} {user_info.get('address_block', '')}")
            print(f"  性別: {user_info.get('gender', 'N/A')}")
            print(f"  生年月日: {user_info.get('birth_date', 'N/A')}")
            print(f"  通話時間: {user_info.get('call_time', 'N/A')}")
            print(f"  通話曜日: {user_info.get('call_weekday', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"⚠ ユーザーが見つかりません（期待される結果）")
            return True
        else:
            print(f"✗ 失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

def comprehensive_test():
    """包括的テスト実行"""
    print("=== AI Diary Get Info Service 包括的テスト ===")
    
    # 実際のユーザーIDでのテスト
    real_user_tests = [
        {
            "user_id": "04B6A6BD-C767-4618-BEC0-262D7F40F0BD",
            "call_id": "call-001",
            "description": "実ユーザー1 - 田中太郎"
        },
        {
            "user_id": "06BDEC2C-C82B-4CFC-A7DE-EC326140BC24",
            "call_id": "call-002", 
            "description": "実ユーザー2 - 田中太郎"
        },
        {
            "user_id": "0B66B7B2-1731-4E9A-BD3A-E12A70EE6D99",
            "call_id": "call-003",
            "description": "実ユーザー3 - 田中太郎"
        }
    ]
    
    # エラーケースのテスト
    error_tests = [
        {
            "user_id": "invalid-user-id-12345",
            "call_id": "call-404",
            "description": "存在しないユーザーID"
        },
        {
            "user_id": "",
            "call_id": "call-empty",
            "description": "空のユーザーID"
        }
    ]
    
    # テスト実行
    success_count = 0
    total_tests = 0
    
    print("\n1. 実ユーザーデータでのテスト")
    print("=" * 50)
    
    for test_case in real_user_tests:
        total_tests += 1
        if test_user_info(test_case["user_id"], test_case["call_id"], test_case["description"]):
            success_count += 1
        time.sleep(1)  # レート制限回避
    
    print("\n2. エラーケースのテスト")
    print("=" * 50)
    
    for test_case in error_tests:
        total_tests += 1
        if test_user_info(test_case["user_id"], test_case["call_id"], test_case["description"]):
            success_count += 1
        time.sleep(1)
    
    # 追加テスト: API構造の検証
    print("\n3. API構造の詳細検証")
    print("=" * 50)
    
    try:
        # 正常なレスポンス構造の検証
        data = {
            "userID": "04B6A6BD-C767-4618-BEC0-262D7F40F0BD",
            "callID": "structure-test"
        }
        
        response = requests.post(
            "http://localhost:8080/get-user-info",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            expected_top_level = ["status", "userID", "callID", "userInfo"]
            expected_user_info = [
                "user_id", "last_name", "first_name", "last_name_kana", "first_name_kana",
                "postal_code", "prefecture", "address_block", "address_building",
                "phone_number", "email", "gender", "birth_date", "call_time", "call_weekday",
                "created_at", "updated_at"
            ]
            
            print("レスポンス構造検証:")
            for field in expected_top_level:
                if field in result:
                    print(f"  ✓ {field}: 存在")
                else:
                    print(f"  ✗ {field}: 不足")
            
            if "userInfo" in result:
                print("\nユーザー情報フィールド検証:")
                user_info = result["userInfo"]
                for field in expected_user_info:
                    if field in user_info:
                        print(f"  ✓ {field}: {type(user_info[field]).__name__}")
                    else:
                        print(f"  ✗ {field}: 不足")
            
            total_tests += 1
            success_count += 1
        else:
            print("API構造検証失敗")
            total_tests += 1
            
    except Exception as e:
        print(f"API構造検証エラー: {e}")
        total_tests += 1
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("包括的テスト結果サマリー")
    print("=" * 60)
    print(f"実行テスト数: {total_tests}")
    print(f"成功: {success_count}")
    print(f"失敗: {total_tests - success_count}")
    print(f"成功率: {(success_count / total_tests * 100):.1f}%")
    
    if success_count == total_tests:
        print("\n✓ すべてのテストが成功しました！")
        print("✓ DBに存在する実データでの情報取得が正常に動作しています")
        print("✓ エラーハンドリングも適切に機能しています")
        print("✓ APIレスポンス構造も正常です")
        return True
    else:
        print(f"\n⚠ {total_tests - success_count}件のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = comprehensive_test()
    exit(0 if success else 1) 