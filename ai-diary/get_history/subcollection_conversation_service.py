"""
サブコレクション構造対応の会話履歴取得サービス
users/{userID}/calls/{callID} 形式
"""
import os
import json
from datetime import datetime
from google.cloud import firestore
from typing import Dict, Optional, Tuple, Any

class SubcollectionConversationHistoryService:
    """
    サブコレクション構造対応の会話履歴取得サービス
    """
    
    def __init__(self):
        """
        Firestore クライアントを初期化
        """
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        self.db = firestore.Client(project=project_id)
    
    def get_user_info(self, user_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        ユーザー情報を取得
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (成功フラグ, ユーザーデータ, エラーコード)
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return False, None, "USER_NOT_FOUND"
            
            user_data = user_doc.to_dict()
            return True, user_data, "SUCCESS"
            
        except Exception as e:
            print(f"ユーザー情報取得エラー: {str(e)}")
            return False, None, "INTERNAL_ERROR"
    
    def get_conversation_by_call_id(self, user_id: str, call_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        指定されたuserIDとcallIDで会話履歴を取得
        
        Args:
            user_id (str): ユーザーID
            call_id (str): 会話ID
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (成功フラグ, 会話データ, エラーコード)
        """
        try:
            # users/{userID}/calls/{callID} のパスで取得
            user_ref = self.db.collection('users').document(user_id)
            call_ref = user_ref.collection('calls').document(call_id)
            call_doc = call_ref.get()
            
            if not call_doc.exists:
                return False, None, "CONVERSATION_NOT_FOUND"
            
            call_data = call_doc.to_dict()
            
            # 念のためuserIDの照合（データ整合性チェック）
            if call_data.get('userID') != user_id:
                return False, None, "USER_MISMATCH"
            
            return True, call_data, "SUCCESS"
            
        except Exception as e:
            print(f"会話履歴取得エラー: {str(e)}")
            return False, None, "INTERNAL_ERROR"
    
    def get_conversation_history(self, user_id: str, call_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        ユーザー認証後、会話履歴を取得するメイン処理
        
        Args:
            user_id (str): ユーザーID
            call_id (str): 会話ID
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (成功フラグ, レスポンスデータ, エラーコード)
        """
        # 1. ユーザー情報取得
        user_success, user_data, user_error = self.get_user_info(user_id)
        if not user_success:
            return False, None, user_error
        
        # 2. 会話履歴取得
        conv_success, conv_data, conv_error = self.get_conversation_by_call_id(user_id, call_id)
        if not conv_success:
            return False, None, conv_error
        
        # 3. レスポンスデータ構築
        response_data = {
            "user_info": {
                "userID": user_data.get('userID'),
                "name": user_data.get('name'),
                "age": user_data.get('age'),
                "gender": user_data.get('gender'),
                "address": user_data.get('address'),
                "phone": user_data.get('phone'),
                "emergency_contact": user_data.get('emergency_contact'),
                "medical_info": user_data.get('medical_info')
            },
            "conversation_history": {
                "callID": conv_data.get('callID'),
                "timestamp": conv_data.get('timestamp'),
                "call_type": conv_data.get('call_type'),
                "status": conv_data.get('status'),
                "duration_seconds": conv_data.get('duration_seconds'),
                "call_start_time": conv_data.get('call_start_time'),
                "call_end_time": conv_data.get('call_end_time'),
                "conversation": conv_data.get('conversation', []),
                "ai_analysis": conv_data.get('ai_analysis'),
                "metadata": conv_data.get('metadata'),
                "tags": conv_data.get('tags', [])
            },
            "retrieved_at": datetime.now().isoformat(),
            "firestore_path": f"users/{user_id}/calls/{call_id}"
        }
        
        return True, response_data, "SUCCESS"
    
    def get_user_all_calls(self, user_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        指定ユーザーのすべての会話履歴を取得
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (成功フラグ, 全会話データ, エラーコード)
        """
        try:
            # ユーザー存在確認
            user_success, user_data, user_error = self.get_user_info(user_id)
            if not user_success:
                return False, None, user_error
            
            # calls サブコレクション内のすべてのドキュメントを取得
            user_ref = self.db.collection('users').document(user_id)
            calls_ref = user_ref.collection('calls')
            calls_docs = calls_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).get()
            
            calls_list = []
            for call_doc in calls_docs:
                call_data = call_doc.to_dict()
                call_data['callID'] = call_doc.id  # ドキュメントIDも含める
                calls_list.append(call_data)
            
            response_data = {
                "user_info": {
                    "userID": user_data.get('userID'),
                    "name": user_data.get('name')
                },
                "calls_count": len(calls_list),
                "calls": calls_list,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return True, response_data, "SUCCESS"
            
        except Exception as e:
            print(f"全会話履歴取得エラー: {str(e)}")
            return False, None, "INTERNAL_ERROR"

def test_subcollection_service():
    """
    サブコレクション構造対応サービスのテスト
    """
    print("=== サブコレクション構造対応サービステスト ===")
    
    service = SubcollectionConversationHistoryService()
    
    # テストデータ
    test_user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    test_call_id = "CA995a950a2b9f6623a5adc987d0b31131"
    
    print(f"\nテスト対象:")
    print(f"  UserID: {test_user_id}")
    print(f"  CallID: {test_call_id}")
    
    # 1. ユーザー情報取得テスト
    print(f"\n--- ユーザー情報取得テスト ---")
    user_success, user_data, user_error = service.get_user_info(test_user_id)
    if user_success:
        print(f"✅ ユーザー情報取得成功")
        print(f"   名前: {user_data.get('name')}")
        print(f"   年齢: {user_data.get('age')}")
    else:
        print(f"❌ ユーザー情報取得失敗: {user_error}")
    
    # 2. 会話履歴取得テスト
    print(f"\n--- 会話履歴取得テスト ---")
    conv_success, conv_data, conv_error = service.get_conversation_by_call_id(test_user_id, test_call_id)
    if conv_success:
        print(f"✅ 会話履歴取得成功")
        print(f"   CallID: {conv_data.get('callID')}")
        print(f"   Status: {conv_data.get('status')}")
        print(f"   会話数: {len(conv_data.get('conversation', []))}")
    else:
        print(f"❌ 会話履歴取得失敗: {conv_error}")
    
    # 3. 統合テスト
    print(f"\n--- 統合テスト ---")
    success, response_data, error_code = service.get_conversation_history(test_user_id, test_call_id)
    if success:
        print(f"✅ 統合テスト成功")
        print(f"   ユーザー: {response_data['user_info']['name']}")
        print(f"   会話ID: {response_data['conversation_history']['callID']}")
        print(f"   Firestoreパス: {response_data['firestore_path']}")
        
        # 会話内容のサンプル表示
        conversations = response_data['conversation_history']['conversation']
        if conversations:
            first_conv = conversations[0]
            print(f"   最初のメッセージ: {first_conv['message'][:50]}...")
    else:
        print(f"❌ 統合テスト失敗: {error_code}")
    
    # 4. 全会話履歴取得テスト
    print(f"\n--- 全会話履歴取得テスト ---")
    all_success, all_data, all_error = service.get_user_all_calls(test_user_id)
    if all_success:
        print(f"✅ 全会話履歴取得成功")
        print(f"   会話履歴数: {all_data['calls_count']}")
        for call in all_data['calls']:
            print(f"     - {call.get('callID')}: {call.get('status')}")
    else:
        print(f"❌ 全会話履歴取得失敗: {all_error}")

if __name__ == "__main__":
    test_subcollection_service() 