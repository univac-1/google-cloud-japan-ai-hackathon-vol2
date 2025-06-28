"""
Firestore サブコレクション構造確認スクリプト
users/{userID}/calls/{callID} の構造を調査
"""
import os
from google.cloud import firestore
import json

def check_subcollection_structure():
    """
    users/{userID}/calls/{callID} の構造を確認
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("=== Firestore サブコレクション構造確認 ===")
        
        # users コレクションを確認
        users_ref = db.collection('users')
        users_docs = users_ref.get()
        
        if not users_docs:
            print("❌ users コレクションが空です")
            return
        
        print(f"📊 users コレクション内のドキュメント数: {len(users_docs)}")
        
        for user_doc in users_docs:
            user_id = user_doc.id
            print(f"\n--- ユーザー: {user_id} ---")
            
            # ユーザードキュメントの基本情報
            user_data = user_doc.to_dict()
            if 'name' in user_data:
                print(f"名前: {user_data['name']}")
            
            # calls サブコレクションを確認
            user_ref = db.collection('users').document(user_id)
            
            # サブコレクション一覧を取得
            subcollections = user_ref.collections()
            subcollection_names = []
            
            for subcollection in subcollections:
                subcollection_names.append(subcollection.id)
                print(f"📁 サブコレクション: {subcollection.id}")
                
                if subcollection.id == 'calls':
                    # calls サブコレクション内のドキュメントを確認
                    calls_docs = subcollection.get()
                    print(f"   📞 calls 内のドキュメント数: {len(calls_docs)}")
                    
                    for call_doc in calls_docs:
                        call_id = call_doc.id
                        call_data = call_doc.to_dict()
                        print(f"     CallID: {call_id}")
                        print(f"     フィールド数: {len(call_data)}")
                        
                        # 主要フィールドを表示
                        key_fields = ['timestamp', 'status', 'duration_seconds', 'conversation']
                        for field in key_fields:
                            if field in call_data:
                                if field == 'conversation' and isinstance(call_data[field], list):
                                    print(f"       {field}: {len(call_data[field])} 会話")
                                else:
                                    print(f"       {field}: {call_data[field]}")
            
            if not subcollection_names:
                print("   サブコレクションなし")
        
        return True
        
    except Exception as e:
        print(f"❌ 構造確認エラー: {str(e)}")
        return False

def search_specific_user_and_call(user_id="4CC0CA6A-657C-4253-99FF-C19219D30AE2", call_id="CA995a950a2b9f6623a5adc987d0b31131"):
    """
    指定されたuserIDとcallIDの組み合わせを検索
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== 指定データ検索 ===")
        print(f"UserID: {user_id}")
        print(f"CallID: {call_id}")
        
        # users/{userID} の確認
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"❌ ユーザー {user_id} が見つかりません")
            return False
        
        print(f"✅ ユーザー {user_id} が見つかりました")
        user_data = user_doc.to_dict()
        if 'name' in user_data:
            print(f"   名前: {user_data['name']}")
        
        # users/{userID}/calls/{callID} の確認
        call_ref = user_ref.collection('calls').document(call_id)
        call_doc = call_ref.get()
        
        if not call_doc.exists:
            print(f"❌ 会話 {call_id} が見つかりません")
            
            # calls サブコレクション内の全ドキュメントを確認
            calls_ref = user_ref.collection('calls')
            calls_docs = calls_ref.get()
            
            if calls_docs:
                print(f"📞 calls サブコレクション内の既存ドキュメント:")
                for doc in calls_docs:
                    print(f"   - {doc.id}")
            else:
                print(f"📞 calls サブコレクションが空です")
            
            return False
        
        print(f"✅ 会話 {call_id} が見つかりました")
        call_data = call_doc.to_dict()
        print(f"   フィールド数: {len(call_data)}")
        
        # 会話内容の詳細を表示
        if 'conversation' in call_data:
            conversations = call_data['conversation']
            if isinstance(conversations, list):
                print(f"   会話数: {len(conversations)}")
                if conversations:
                    first_msg = conversations[0]
                    if isinstance(first_msg, dict) and 'message' in first_msg:
                        print(f"   最初のメッセージ: {first_msg['message'][:50]}...")
        
        if 'timestamp' in call_data:
            print(f"   タイムスタンプ: {call_data['timestamp']}")
        
        if 'status' in call_data:
            print(f"   ステータス: {call_data['status']}")
        
        return True, user_data, call_data
        
    except Exception as e:
        print(f"❌ 指定データ検索エラー: {str(e)}")
        return False, None, None

if __name__ == "__main__":
    print("Firestore サブコレクション構造確認を開始します...")
    
    # 1. 全体構造確認
    check_subcollection_structure()
    
    # 2. 指定されたユーザーとCallIDの組み合わせ確認
    search_specific_user_and_call()
    
    print("\nFirestore サブコレクション構造確認が完了しました。") 