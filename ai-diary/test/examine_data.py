"""
既存データの構造調査スクリプト
"""
import os
from google.cloud import firestore
import json

def examine_users_collection():
    """
    users コレクションの構造を詳しく調査
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"=== Users コレクション詳細調査 ===")
        
        users_ref = db.collection('users')
        users_docs = users_ref.limit(5).get()  # 最初の5件を取得
        
        if not users_docs:
            print("❌ users コレクションが空です")
            return False
        
        print(f"📊 取得したドキュメント数: {len(users_docs)}")
        
        for i, doc in enumerate(users_docs, 1):
            print(f"\n--- ユーザー {i} ---")
            print(f"ドキュメントID: {doc.id}")
            
            data = doc.to_dict()
            print(f"フィールド数: {len(data)}")
            
            # 各フィールドの詳細を表示
            for field_name, field_value in data.items():
                field_type = type(field_value).__name__
                if isinstance(field_value, (str, int, float, bool)):
                    print(f"  {field_name} ({field_type}): {field_value}")
                elif isinstance(field_value, list):
                    print(f"  {field_name} ({field_type}): {len(field_value)} 要素")
                    if field_value and len(field_value) > 0:
                        print(f"    最初の要素: {field_value[0]}")
                elif isinstance(field_value, dict):
                    print(f"  {field_name} ({field_type}): {len(field_value)} キー")
                    print(f"    キー: {list(field_value.keys())}")
                else:
                    print(f"  {field_name} ({field_type}): {str(field_value)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Users コレクション調査エラー: {str(e)}")
        return False

def examine_user_subcollections(user_id=None):
    """
    ユーザーのサブコレクションを調査（会話履歴が含まれている可能性）
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== ユーザーサブコレクション調査 ===")
        
        # user_id が指定されていない場合、最初のユーザーを使用
        if not user_id:
            users_ref = db.collection('users')
            users_docs = users_ref.limit(1).get()
            if not users_docs:
                print("❌ ユーザーが見つかりません")
                return False
            user_id = users_docs[0].id
        
        print(f"調査対象ユーザーID: {user_id}")
        
        user_ref = db.collection('users').document(user_id)
        
        # サブコレクションを確認
        subcollections = user_ref.collections()
        subcollection_names = []
        
        for subcollection in subcollections:
            subcollection_names.append(subcollection.id)
            print(f"📁 サブコレクション: {subcollection.id}")
            
            # サブコレクション内のドキュメントを確認
            docs = subcollection.limit(3).get()
            if docs:
                print(f"  ドキュメント数: {len(docs)}+ 件")
                first_doc = docs[0]
                print(f"  サンプルドキュメントID: {first_doc.id}")
                
                sample_data = first_doc.to_dict()
                print(f"  サンプルフィールド: {list(sample_data.keys())}")
                
                # callID フィールドがあるかチェック
                if 'callID' in sample_data:
                    print(f"  ✅ callID フィールドが存在: {sample_data['callID']}")
                if 'call_id' in sample_data:
                    print(f"  ✅ call_id フィールドが存在: {sample_data['call_id']}")
            else:
                print(f"  ドキュメントが見つかりません")
        
        if not subcollection_names:
            print("サブコレクションが見つかりません")
        
        return True
        
    except Exception as e:
        print(f"❌ サブコレクション調査エラー: {str(e)}")
        return False

def search_call_id_in_firestore(call_id="test_call_id"):
    """
    Firestore 全体で callID を検索
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== callID 検索: {call_id} ===")
        
        # users コレクション内を検索
        print("Users コレクションを検索中...")
        users_ref = db.collection('users')
        
        # callID フィールドで検索
        query1 = users_ref.where('callID', '==', call_id).limit(5)
        docs1 = query1.get()
        
        # call_id フィールドで検索
        query2 = users_ref.where('call_id', '==', call_id).limit(5)
        docs2 = query2.get()
        
        if docs1:
            print(f"✅ callID フィールドで {len(docs1)} 件見つかりました")
        if docs2:
            print(f"✅ call_id フィールドで {len(docs2)} 件見つかりました")
        
        if not docs1 and not docs2:
            print(f"❌ callID '{call_id}' が見つかりませんでした")
        
        return True
        
    except Exception as e:
        print(f"❌ callID 検索エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("既存データ構造調査を開始します...")
    
    # Users コレクション調査
    if examine_users_collection():
        print("\n" + "="*50)
        
        # サブコレクション調査
        examine_user_subcollections()
        
        print("\n" + "="*50)
        
        # CallID 検索テスト
        search_call_id_in_firestore()
    
    print("\n既存データ構造調査が完了しました。") 