"""
Firestore 全体のコレクション検索スクリプト
指定されたドキュメントIDを探して、会話履歴がどこに格納されているかを調査
"""
import os
from google.cloud import firestore
import json

def search_document_across_collections(target_doc_id="4CC0CA6A-657C-4253-99FF-C19219D30AE2"):
    """
    全コレクションから指定されたドキュメント ID を検索
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"=== 全コレクション検索 ===")
        print(f"対象ドキュメントID: {target_doc_id}")
        
        # よくある会話履歴コレクション名を試す
        potential_collections = [
            'users',
            'conversations', 
            'calls',
            'chat_history',
            'user_conversations',
            'conversation_logs',
            'sessions',
            'call_sessions',
            'ai_calls',
            'phone_calls',
            'user_calls'
        ]
        
        found_documents = []
        
        for collection_name in potential_collections:
            print(f"\n📁 {collection_name} コレクションを検索中...")
            
            try:
                collection_ref = db.collection(collection_name)
                
                # 直接ドキュメント ID で検索
                doc_ref = collection_ref.document(target_doc_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    print(f"✅ {collection_name}/{target_doc_id} で見つかりました！")
                    doc_data = doc.to_dict()
                    found_documents.append({
                        'collection': collection_name,
                        'document_id': target_doc_id,
                        'data': doc_data
                    })
                    
                    print(f"   フィールド数: {len(doc_data)}")
                    print(f"   主要フィールド: {list(doc_data.keys())[:10]}")
                    
                    # 会話履歴らしきフィールドをチェック
                    conversation_indicators = []
                    for field_name in doc_data.keys():
                        if any(keyword in field_name.lower() for keyword in ['call', 'conversation', 'chat', 'history', 'message', 'transcript']):
                            conversation_indicators.append(field_name)
                    
                    if conversation_indicators:
                        print(f"   🎯 会話履歴候補フィールド: {conversation_indicators}")
                else:
                    print(f"   ❌ 見つかりませんでした")
                    
                # コレクション内の全ドキュメントもチェック（最初の5件のみ）
                all_docs = collection_ref.limit(5).get()
                if all_docs:
                    print(f"   📊 {collection_name} に {len(all_docs)}+ ドキュメントが存在")
                    for i, d in enumerate(all_docs):
                        print(f"     [{i+1}] {d.id}")
                        if target_doc_id.lower() in d.id.lower():
                            print(f"        🔍 部分一致の可能性")
                            
            except Exception as e:
                print(f"   ⚠️  コレクション {collection_name} へのアクセスエラー: {str(e)}")
        
        return found_documents
        
    except Exception as e:
        print(f"❌ 検索エラー: {str(e)}")
        return []

def search_by_partial_id(partial_id):
    """
    部分的なIDでドキュメントを検索
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== 部分ID検索: {partial_id} ===")
        
        collections_to_search = ['users', 'conversations', 'calls', 'sessions']
        
        for collection_name in collections_to_search:
            try:
                collection_ref = db.collection(collection_name)
                docs = collection_ref.get()
                
                matching_docs = []
                for doc in docs:
                    if partial_id.lower() in doc.id.lower():
                        matching_docs.append(doc)
                
                if matching_docs:
                    print(f"\n📁 {collection_name} で部分一致発見:")
                    for doc in matching_docs:
                        print(f"   🎯 {doc.id}")
                        data = doc.to_dict()
                        print(f"      フィールド数: {len(data)}")
                        print(f"      主要フィールド: {list(data.keys())[:5]}")
                        
            except Exception as e:
                print(f"   ⚠️  {collection_name} 検索エラー: {str(e)}")
                
    except Exception as e:
        print(f"❌ 部分ID検索エラー: {str(e)}")

def analyze_found_documents(found_documents):
    """
    見つかったドキュメントを詳しく分析
    """
    if not found_documents:
        print(f"\n❌ 対象ドキュメントが見つかりませんでした")
        return
    
    print(f"\n=== 見つかったドキュメントの詳細分析 ===")
    
    for doc_info in found_documents:
        collection_name = doc_info['collection']
        document_id = doc_info['document_id']
        data = doc_info['data']
        
        print(f"\n📄 {collection_name}/{document_id}")
        print(f"フィールド数: {len(data)}")
        
        # 各フィールドの詳細分析
        for field_name, field_value in data.items():
            field_type = type(field_value).__name__
            
            if isinstance(field_value, list):
                print(f"  {field_name} ({field_type}): {len(field_value)} 要素")
                if field_value and len(field_value) > 0:
                    first_item = field_value[0]
                    if isinstance(first_item, dict):
                        print(f"    最初の要素キー: {list(first_item.keys())}")
                        # callID を探す
                        for key in first_item.keys():
                            if 'call' in key.lower() or 'id' in key.lower():
                                print(f"    🔑 {key}: {first_item[key]}")
                    
            elif isinstance(field_value, dict):
                print(f"  {field_name} ({field_type}): {len(field_value)} キー")
                print(f"    キー: {list(field_value.keys())[:5]}")
                
            elif isinstance(field_value, str):
                display_value = field_value[:100] + "..." if len(field_value) > 100 else field_value
                print(f"  {field_name} ({field_type}): {display_value}")
                
            else:
                print(f"  {field_name} ({field_type}): {str(field_value)}")

def list_all_collections():
    """
    プロジェクト内の全コレクションを一覧表示（実際には制限があるため、試せる範囲で）
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== プロジェクト内コレクション概要 ===")
        
        # 実際に試せるコレクション名
        test_collections = [
            'users', 'conversations', 'calls', 'sessions', 'chats', 
            'messages', 'history', 'logs', 'data', 'records',
            'ai_calls', 'phone_calls', 'user_data', 'call_history'
        ]
        
        existing_collections = []
        
        for collection_name in test_collections:
            try:
                collection_ref = db.collection(collection_name)
                docs = collection_ref.limit(1).get()
                
                if docs:
                    existing_collections.append(collection_name)
                    doc_count = len(collection_ref.get())
                    print(f"✅ {collection_name}: {doc_count} ドキュメント")
                    
            except Exception as e:
                # コレクションが存在しない場合は無視
                pass
        
        print(f"\n📊 見つかったコレクション数: {len(existing_collections)}")
        return existing_collections
        
    except Exception as e:
        print(f"❌ コレクション一覧取得エラー: {str(e)}")
        return []

if __name__ == "__main__":
    print("Firestore 全体検索を開始します...")
    
    target_doc_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    
    # 1. 全コレクション概要確認
    existing_collections = list_all_collections()
    
    # 2. 指定ドキュメント ID を全コレクションで検索
    found_documents = search_document_across_collections(target_doc_id)
    
    # 3. 見つかったドキュメントの詳細分析
    analyze_found_documents(found_documents)
    
    # 4. 部分ID検索も試す
    partial_searches = ["4CC0CA6A", "657C-4253", "99FF-C19219D30AE2"]
    for partial in partial_searches:
        search_by_partial_id(partial)
    
    print(f"\nFirestore 全体検索が完了しました。")
    
    if not found_documents:
        print(f"\n💡 推奨アクション:")
        print(f"1. ドキュメント ID を再確認してください")
        print(f"2. 別のプロジェクトにデータがある可能性があります")
        print(f"3. コレクション名が異なる可能性があります")
        print(f"4. データベースが異なる可能性があります（別のFirestoreインスタンス等）") 