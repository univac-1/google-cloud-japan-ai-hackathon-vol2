#!/usr/bin/env python3
"""
AI Diary Service 統合テストスクリプト
DB接続とGemini API呼び出しを含む完全なテスト
"""

import os
import sys
import requests
import json

# テスト用パラメータ
TEST_USER_ID = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
TEST_CALL_ID = "CA995a950a2b9f6623a5adc987d0b31131"
API_BASE_URL = "http://localhost:8080"

def test_db_connection():
    """DB接続テスト"""
    print("🔄 DB接続テストを開始します...")
    
    try:
        from get_info.db_connection import test_connection
        success, message = test_connection()
        
        if success:
            print("✅ DB接続テスト成功!")
            print(f"   メッセージ: {message}")
            return True
        else:
            print(f"❌ DB接続テスト失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ DB接続テスト中にエラーが発生しました: {str(e)}")
        return False

def test_user_info_retrieval():
    """ユーザー情報取得テスト"""
    print(f"\n🔄 ユーザー情報取得テストを開始します (userID: {TEST_USER_ID})...")
    
    try:
        from get_info.user_service import get_user_info
        
        success, user_info, error_code = get_user_info(TEST_USER_ID)
        
        if success:
            print("✅ ユーザー情報取得成功!")
            print(f"   取得されたユーザー情報:")
            for key, value in user_info.items():
                print(f"     {key}: {value}")
            return True, user_info
        else:
            print(f"❌ ユーザー情報取得失敗: エラーコード {error_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ ユーザー情報取得テスト中にエラーが発生しました: {str(e)}")
        return False, None

def test_conversation_history():
    """会話履歴取得テスト"""
    print(f"\n🔄 会話履歴取得テストを開始します (userID: {TEST_USER_ID}, callID: {TEST_CALL_ID})...")
    
    try:
        from get_history.conversation_service import get_conversation_history
        
        success, conversation_data, error_code = get_conversation_history(TEST_USER_ID, TEST_CALL_ID)
        
        if success:
            print("✅ 会話履歴取得成功!")
            print(f"   取得された会話履歴:")
            if 'conversation' in conversation_data:
                for i, conv in enumerate(conversation_data['conversation'][:3]):  # 最初の3件のみ表示
                    print(f"     {i+1}. {conv.get('role', 'unknown')}: {conv.get('text', '')[:50]}...")
                if len(conversation_data['conversation']) > 3:
                    print(f"     ... 他 {len(conversation_data['conversation']) - 3} 件")
            return True, conversation_data
        else:
            print(f"❌ 会話履歴取得失敗: エラーコード {error_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ 会話履歴取得テスト中にエラーが発生しました: {str(e)}")
        return False, None

def test_diary_generation_with_real_data(user_info, conversation_data):
    """実データを使用した日記生成テスト"""
    print("\n🔄 実データを使用した日記生成テストを開始します...")
    
    try:
        from create_diary_entry import DiaryGenerator
        
        generator = DiaryGenerator()
        success, diary_text, error = generator.generate_diary_entry(user_info, conversation_data)
        
        if success:
            print("✅ 日記生成テスト成功!")
            print("\n📄 生成された日記:")
            print("=" * 60)
            print(diary_text)
            print("=" * 60)
            return True
        else:
            print(f"❌ 日記生成テスト失敗: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 日記生成テスト中にエラーが発生しました: {str(e)}")
        return False
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