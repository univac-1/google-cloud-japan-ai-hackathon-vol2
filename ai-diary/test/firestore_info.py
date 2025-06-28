"""
Firestore リソース情報確認・記録スクリプト
"""
import os
from google.cloud import firestore
from google.cloud.firestore_v1 import Client

def get_firestore_info():
    """
    Firestore のリソース情報を取得し、記録する
    """
    try:
        # 環境変数からプロジェクトIDを取得
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        
        # Firestore クライアントを初期化
        db = firestore.Client(project=project_id)
        
        print(f"=== Firestore リソース情報 ===")
        print(f"プロジェクトID: {project_id}")
        print(f"データベース: (default)")
        print(f"リージョン: asia-northeast1")
        
        # コレクション一覧を取得（実際にあるコレクションをチェック）
        collections = db.collections()
        collection_names = []
        
        print(f"\n=== 既存コレクション ===")
        for collection in collections:
            collection_names.append(collection.id)
            print(f"- {collection.id}")
        
        if not collection_names:
            print("コレクションが存在しません")
        
        # テストデータでコレクション作成をテスト
        test_collection_ref = db.collection('test_connection')
        
        # テストドキュメントを作成
        test_doc_ref = test_collection_ref.document('test_doc')
        test_doc_ref.set({
            'test': True,
            'message': 'Firestore接続テスト',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # テストドキュメントを読み取り
        test_doc = test_doc_ref.get()
        if test_doc.exists:
            print(f"\n=== 接続テスト結果 ===")
            print(f"✅ Firestore への書き込み・読み取りが正常に動作しています")
            print(f"テストドキュメント内容: {test_doc.to_dict()}")
        
        # テストドキュメントを削除
        test_doc_ref.delete()
        print(f"🗑️ テストドキュメントを削除しました")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore 接続エラー: {str(e)}")
        return False

def check_conversation_collections():
    """
    会話履歴関連のコレクションを確認
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== 会話履歴コレクション確認 ===")
        
        # 想定される会話履歴コレクション名
        expected_collections = [
            'conversations',
            'chat_history', 
            'calls',
            'user_conversations',
            'conversation_logs'
        ]
        
        for collection_name in expected_collections:
            collection_ref = db.collection(collection_name)
            docs = collection_ref.limit(1).get()
            
            if docs:
                print(f"✅ {collection_name}: {len(docs)} ドキュメント以上存在")
                # 最初のドキュメントの構造を確認
                first_doc = docs[0]
                print(f"   サンプルドキュメントID: {first_doc.id}")
                print(f"   フィールド: {list(first_doc.to_dict().keys())}")
            else:
                print(f"❌ {collection_name}: コレクションが存在しないか空です")
        
        return True
        
    except Exception as e:
        print(f"❌ 会話履歴コレクション確認エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("Firestore リソース情報確認を開始します...")
    
    # 基本的なリソース情報確認
    if get_firestore_info():
        print("\n" + "="*50)
        # 会話履歴コレクション確認
        check_conversation_collections()
    
    print("\nFirestore リソース情報確認が完了しました。") 