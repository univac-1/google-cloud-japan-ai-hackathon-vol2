#!/usr/bin/env python3
"""
AI Diary Get Info Service - 実データテストスクリプト
実際のデータベースのユーザーIDを使ってAPIをテストします
"""

import requests
import json
import sys
import os

# 設定
API_BASE_URL = "http://localhost:8080"

def test_health_check():
    """ヘルスチェックテスト"""
    print("=== ヘルスチェックテスト ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"エラー: {e}")
        return False

def test_db_connection():
    """データベース接続テスト"""
    print("\n=== データベース接続テスト ===")
    try:
        response = requests.get(f"{API_BASE_URL}/test-db")
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"エラー: {e}")
        return False

def test_user_info_api(user_id, call_id="test-call-001"):
    """ユーザー情報取得APIテスト"""
    print(f"\n=== ユーザー情報取得APIテスト (user_id: {user_id}) ===")
    try:
        data = {
            "userID": user_id,
            "callID": call_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/get-user-info",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"ステータスコード: {response.status_code}")
        print(f"リクエストデータ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✓ API呼び出し成功")
            print(f"レスポンス:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # レスポンス構造の検証
            expected_fields = ["status", "userID", "callID", "userInfo"]
            for field in expected_fields:
                if field in response_data:
                    print(f"✓ {field} フィールド存在")
                else:
                    print(f"✗ {field} フィールドが不足")
            
            # ユーザー情報の詳細検証
            if "userInfo" in response_data:
                user_info = response_data["userInfo"]
                user_fields = ["user_id", "last_name", "first_name", "phone_number", "email"]
                print("\nユーザー情報詳細:")
                for field in user_fields:
                    if field in user_info:
                        print(f"  {field}: {user_info[field]}")
                    else:
                        print(f"  {field}: (不足)")
            
            return True
        else:
            print(f"✗ API呼び出し失敗")
            print(f"エラーレスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"エラー: {e}")
        return False

def test_invalid_user_id():
    """存在しないユーザーIDでのテスト"""
    print(f"\n=== 存在しないユーザーIDテスト ===")
    try:
        data = {
            "userID": "invalid-user-id-12345",
            "callID": "test-call-002"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/get-user-info",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        
        if response.status_code == 404:
            print("✓ 存在しないユーザーに対して正しく404を返している")
            return True
        else:
            print("✗ 存在しないユーザーに対するレスポンスが不正")
            return False
            
    except Exception as e:
        print(f"エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("AI Diary Get Info Service - 実データテスト開始")
    print("=" * 60)
    
    # 実際のユーザーIDを設定（DBから取得したもの）
    test_user_ids = [
        "04B6A6BD-C767-4618-BEC0-262D7F40F0BD",  # 田中太郎
        "06BDEC2C-C82B-4CFC-A7DE-EC326140BC24",  # 田中太郎
        "0B66B7B2-1731-4E9A-BD3A-E12A70EE6D99"   # 田中太郎
    ]
    
    # テスト実行
    tests_passed = 0
    total_tests = 0
    
    # 1. ヘルスチェック
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # 2. データベース接続テスト
    total_tests += 1
    if test_db_connection():
        tests_passed += 1
    
    # 3. 実データでのユーザー情報取得テスト
    for user_id in test_user_ids:
        total_tests += 1
        if test_user_info_api(user_id):
            tests_passed += 1
    
    # 4. 存在しないユーザーIDテスト
    total_tests += 1
    if test_invalid_user_id():
        tests_passed += 1
    
    # テスト結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print(f"成功: {tests_passed}/{total_tests} テスト")
    print(f"成功率: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("✓ すべてのテストが成功しました！")
        return 0
    else:
        print("✗ 一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 