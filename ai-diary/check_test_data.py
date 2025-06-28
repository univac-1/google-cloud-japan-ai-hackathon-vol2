#!/usr/bin/env python3
"""
テスト用のユーザー情報と会話履歴データを確認・作成するスクリプト
"""
import os
import sys
import json

# 環境変数を読み込み
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()
sys.path.append(os.path.dirname(__file__))

from get_info.user_service import get_user_info
from get_history.subcollection_conversation_service import SubcollectionConversationHistoryService

def check_test_data():
    """テストデータの存在確認"""
    print("=== テストデータ確認 ===")
    
    # テスト用のユーザーID
    test_user_ids = ["test-user-123", "user123", "1", "test-user-1"]
    
    print("1. ユーザー情報確認:")
    available_users = []
    for user_id in test_user_ids:
        user_info = get_user_info(user_id)
        if user_info:
            print(f"✅ {user_id}: {user_info}")
            available_users.append(user_id)
        else:
            print(f"❌ {user_id}: データなし")
    
    if not available_users:
        print("⚠️ 利用可能なユーザーデータがありません")
        return None, None
    
    # 最初の利用可能なユーザーで会話履歴をチェック
    test_user_id = available_users[0]
    print(f"\n2. 会話履歴確認 (ユーザー: {test_user_id}):")
    
    # テスト用のコールID
    test_call_ids = ["test-call-456", "call456", "1", "test-call-1"]
    
    service = SubcollectionConversationHistoryService()
    available_calls = []
    
    for call_id in test_call_ids:
        success, conversation_data, error_code = service.get_conversation_history(test_user_id, call_id)
        if success:
            print(f"✅ {call_id}: 会話履歴あり")
            available_calls.append(call_id)
        else:
            print(f"❌ {call_id}: {error_code}")
    
    if available_calls:
        return test_user_id, available_calls[0]
    else:
        print("⚠️ 利用可能な会話履歴がありません")
        return test_user_id, None

if __name__ == "__main__":
    user_id, call_id = check_test_data()
    if user_id and call_id:
        print(f"\n✅ テスト可能: userID={user_id}, callID={call_id}")
    elif user_id:
        print(f"\n⚠️ ユーザーは存在するが会話履歴なし: userID={user_id}")
    else:
        print("\n❌ テスト用データが不足しています")
