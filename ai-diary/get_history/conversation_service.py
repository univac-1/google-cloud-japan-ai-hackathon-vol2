"""
会話履歴取得サービス
ユーザー情報取得後、callIDを使って会話履歴を取得する処理
"""
import os
from google.cloud import firestore
from datetime import datetime
from typing import Dict, List, Optional, Any

class ConversationHistoryService:
    """会話履歴取得サービスクラス"""
    
    def __init__(self):
        """Firestore クライアントを初期化"""
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        self.db = firestore.Client(project=self.project_id)
        
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ユーザー情報を取得
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Optional[Dict[str, Any]]: ユーザー情報、見つからない場合はNone
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['user_id'] = user_doc.id
                return user_data
            else:
                return None
                
        except Exception as e:
            print(f"ユーザー情報取得エラー: {str(e)}")
            return None
    
    def get_conversation_by_call_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        callIDを使って会話履歴を取得
        
        Args:
            call_id (str): 呼び出しID
            
        Returns:
            Optional[Dict[str, Any]]: 会話履歴、見つからない場合はNone
        """
        try:
            # conversations コレクションから call_id で検索
            conversations_ref = self.db.collection('conversations')
            query = conversations_ref.where('call_id', '==', call_id).limit(1)
            results = query.get()
            
            if results:
                conversation_doc = results[0]
                conversation_data = conversation_doc.to_dict()
                conversation_data['document_id'] = conversation_doc.id
                return conversation_data
            else:
                return None
                
        except Exception as e:
            print(f"会話履歴取得エラー: {str(e)}")
            return None
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ユーザーの会話履歴一覧を取得
        
        Args:
            user_id (str): ユーザーID
            limit (int): 取得件数の上限
            
        Returns:
            List[Dict[str, Any]]: 会話履歴のリスト
        """
        try:
            conversations_ref = self.db.collection('conversations')
            query = conversations_ref.where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            results = query.get()
            
            conversations = []
            for doc in results:
                conversation_data = doc.to_dict()
                conversation_data['document_id'] = doc.id
                conversations.append(conversation_data)
            
            return conversations
            
        except Exception as e:
            print(f"ユーザー会話履歴取得エラー: {str(e)}")
            return []
    
    def get_conversation_history(self, user_id: str, call_id: str) -> Dict[str, Any]:
        """
        ユーザー情報取得後、callIDを使って会話履歴を取得するメイン処理
        
        Args:
            user_id (str): ユーザーID
            call_id (str): 呼び出しID
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            # 1. ユーザー情報を取得
            user_info = self.get_user_info(user_id)
            if not user_info:
                return {
                    'status': 'error',
                    'error_code': 'USER_NOT_FOUND',
                    'message': f'ユーザーID {user_id} が見つかりません',
                    'user_id': user_id,
                    'call_id': call_id
                }
            
            # 2. callIDで会話履歴を取得
            conversation = self.get_conversation_by_call_id(call_id)
            if not conversation:
                return {
                    'status': 'error',
                    'error_code': 'CONVERSATION_NOT_FOUND',
                    'message': f'callID {call_id} の会話履歴が見つかりません',
                    'user_id': user_id,
                    'call_id': call_id,
                    'user_info': user_info
                }
            
            # 3. 成功レスポンス
            return {
                'status': 'success',
                'user_id': user_id,
                'call_id': call_id,
                'user_info': user_info,
                'conversation': conversation,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_code': 'INTERNAL_ERROR',
                'message': f'内部エラーが発生しました: {str(e)}',
                'user_id': user_id,
                'call_id': call_id
            }

def get_conversation_history(user_id: str, call_id: str) -> Dict[str, Any]:
    """
    会話履歴取得のエントリーポイント関数
    
    Args:
        user_id (str): ユーザーID
        call_id (str): 呼び出しID
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    service = ConversationHistoryService()
    return service.get_conversation_history(user_id, call_id)

# テスト用の関数
def test_conversation_service():
    """会話履歴取得サービスのテスト"""
    print("=== 会話履歴取得サービステスト ===")
    
    service = ConversationHistoryService()
    
    # テストケース1: 正常なケース
    print("\n1. 正常なケース")
    result1 = service.get_conversation_history('user001', 'call_001_20241201_morning')
    print(f"ステータス: {result1['status']}")
    if result1['status'] == 'success':
        print(f"ユーザー名: {result1['user_info']['name']}")
        print(f"会話数: {len(result1['conversation']['conversation'])}")
    
    # テストケース2: 存在しないユーザー
    print("\n2. 存在しないユーザー")
    result2 = service.get_conversation_history('user999', 'call_001_20241201_morning')
    print(f"ステータス: {result2['status']}")
    print(f"エラーコード: {result2['error_code']}")
    
    # テストケース3: 存在しないcallID
    print("\n3. 存在しないcallID")
    result3 = service.get_conversation_history('user001', 'call_999_invalid')
    print(f"ステータス: {result3['status']}")
    print(f"エラーコード: {result3['error_code']}")
    
    # テストケース4: ユーザーIDミスマッチ
    print("\n4. ユーザーIDミスマッチ")
    result4 = service.get_conversation_history('user002', 'call_001_20241201_morning')
    print(f"ステータス: {result4['status']}")
    print(f"エラーコード: {result4['error_code']}")

if __name__ == "__main__":
    test_conversation_service() 