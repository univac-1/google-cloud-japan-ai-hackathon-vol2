"""
実際の既存会話履歴データ確認スクリプト
"""
import os
from google.cloud import firestore
import json
from datetime import datetime

def list_all_users():
    """
    users コレクション内の全ドキュメントを一覧表示
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"=== Users コレクション全体確認 ===")
        
        users_ref = db.collection('users')
        users_docs = users_ref.get()
        
        if not users_docs:
            print("❌ users コレクションが空です")
            return []
        
        print(f"📊 見つかったドキュメント数: {len(users_docs)}")
        
        user_ids = []
        for i, doc in enumerate(users_docs):
            user_ids.append(doc.id)
            data = doc.to_dict()
            print(f"\n--- ユーザー {i+1} ---")
            print(f"ドキュメントID: {doc.id}")
            print(f"フィールド数: {len(data)}")
            
            # 基本情報のみ表示
            basic_fields = ['name', 'age', 'phone', 'email', 'created_at']
            for field in basic_fields:
                if field in data:
                    print(f"  {field}: {data[field]}")
        
        return user_ids
        
    except Exception as e:
        print(f"❌ Users コレクション確認エラー: {str(e)}")
        return []

def check_specific_user_document(user_doc_id):
    """
    指定されたユーザードキュメントの詳細を確認
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print(f"\n=== 指定ユーザードキュメント詳細確認 ===")
        print(f"ドキュメントID: {user_doc_id}")
        
        # 指定されたドキュメントを取得
        user_ref = db.collection('users').document(user_doc_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"❌ ドキュメント {user_doc_id} が見つかりません")
            return False, None, []
        
        user_data = user_doc.to_dict()
        print(f"✅ ドキュメントが見つかりました")
        print(f"フィールド数: {len(user_data)}")
        
        # 各フィールドの詳細を表示
        print(f"\n--- フィールド詳細 ---")
        for field_name, field_value in user_data.items():
            field_type = type(field_value).__name__
            
            if isinstance(field_value, (str, int, float, bool)):
                display_value = str(field_value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                print(f"{field_name} ({field_type}): {display_value}")
                
            elif isinstance(field_value, list):
                print(f"{field_name} ({field_type}): {len(field_value)} 要素")
                if field_value and len(field_value) > 0:
                    print(f"  最初の要素タイプ: {type(field_value[0]).__name__}")
                    if isinstance(field_value[0], dict):
                        print(f"  最初の要素キー: {list(field_value[0].keys())[:5]}")
                    
            elif isinstance(field_value, dict):
                print(f"{field_name} ({field_type}): {len(field_value)} キー")
                print(f"  キー: {list(field_value.keys())[:10]}")
                
            else:
                print(f"{field_name} ({field_type}): {str(field_value)[:100]}...")
        
        # 会話履歴らしきフィールドを特定
        print(f"\n--- 会話履歴候補フィールド ---")
        conversation_fields = []
        
        for field_name, field_value in user_data.items():
            if any(keyword in field_name.lower() for keyword in ['call', 'conversation', 'chat', 'history', 'message']):
                conversation_fields.append(field_name)
                print(f"📞 {field_name}: {type(field_value).__name__}")
                
                if isinstance(field_value, list) and len(field_value) > 0:
                    print(f"   配列の長さ: {len(field_value)}")
                    sample_item = field_value[0]
                    if isinstance(sample_item, dict):
                        print(f"   サンプル要素キー: {list(sample_item.keys())}")
                        # callID があるかチェック
                        for key in sample_item.keys():
                            if 'call' in key.lower():
                                print(f"   ✅ callID候補: {key} = {sample_item[key]}")
        
        if not conversation_fields:
            print("❌ 会話履歴候補フィールドが見つかりません")
        
        # サブコレクションも確認
        print(f"\n--- サブコレクション確認 ---")
        subcollections = user_ref.collections()
        subcollection_names = []
        
        for subcollection in subcollections:
            subcollection_names.append(subcollection.id)
            print(f"📁 サブコレクション: {subcollection.id}")
            
            # サブコレクション内のドキュメントを確認
            docs = subcollection.limit(3).get()
            if docs:
                print(f"   ドキュメント数: {len(docs)}+ 件")
                first_doc = docs[0]
                print(f"   サンプルドキュメントID: {first_doc.id}")
                
                sample_data = first_doc.to_dict()
                print(f"   サンプルフィールド: {list(sample_data.keys())}")
                
                # callID フィールドがあるかチェック
                for key in sample_data.keys():
                    if 'call' in key.lower():
                        print(f"   ✅ callID候補: {key} = {sample_data[key]}")
            else:
                print(f"   ドキュメントが見つかりません")
        
        if not subcollection_names:
            print("サブコレクションが見つかりません")
        
        return True, user_data, conversation_fields
        
    except Exception as e:
        print(f"❌ ドキュメント確認エラー: {str(e)}")
        return False, None, []

def extract_call_ids_from_data(user_data, conversation_fields):
    """
    ユーザーデータから callID を抽出
    """
    print(f"\n=== callID 抽出処理 ===")
    
    call_ids = []
    
    for field_name in conversation_fields:
        field_value = user_data.get(field_name)
        
        if isinstance(field_value, list):
            print(f"\n📋 {field_name} から callID を抽出中...")
            
            for i, item in enumerate(field_value[:5]):  # 最初の5件のみ確認
                if isinstance(item, dict):
                    # callID らしきフィールドを探す
                    for key, value in item.items():
                        if 'call' in key.lower() and isinstance(value, str):
                            call_ids.append(value)
                            print(f"   [{i}] {key}: {value}")
                            
                    # ID フィールドも確認
                    if 'id' in item:
                        call_ids.append(item['id'])
                        print(f"   [{i}] id: {item['id']}")
    
    # 重複を除去
    unique_call_ids = list(set(call_ids))
    print(f"\n🎯 発見された callID 候補: {len(unique_call_ids)} 件")
    for call_id in unique_call_ids:
        print(f"   - {call_id}")
    
    return unique_call_ids

def test_conversation_retrieval_with_real_data(user_id, call_ids):
    """
    実際のデータで会話履歴取得をテスト
    """
    print(f"\n=== 実データでの会話履歴取得テスト ===")
    print(f"ユーザーID: {user_id}")
    
    # 既存のサービスを使用
    from conversation_service import ConversationHistoryService
    
    service = ConversationHistoryService()
    
    for i, call_id in enumerate(call_ids[:3]):  # 最初の3件をテスト
        print(f"\n--- テスト {i+1}: callID = {call_id} ---")
        
        # 既存のサービスでテスト
        result = service.get_conversation_history(user_id, call_id)
        
        print(f"ステータス: {result['status']}")
        if result['status'] == 'success':
            conversation = result.get('conversation', {})
            print(f"✅ 取得成功")
            print(f"   会話数: {len(conversation.get('conversation', []))}")
            print(f"   持続時間: {conversation.get('duration_seconds', 'N/A')}秒")
        else:
            print(f"❌ 取得失敗: {result.get('error_code', 'UNKNOWN')} - {result.get('message', 'No message')}")

if __name__ == "__main__":
    print("実際の既存会話履歴データ確認を開始します...")
    
    # まず users コレクション全体を確認
    user_ids = list_all_users()
    
    if not user_ids:
        print("\n❌ users コレクションにドキュメントが見つかりません")
        exit(1)
    
    # 指定されたドキュメントIDがあるかチェック
    target_user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    
    if target_user_id in user_ids:
        print(f"\n✅ 指定されたドキュメント {target_user_id} が見つかりました")
        # 指定されたドキュメントを詳細確認
        success, user_data, conversation_fields = check_specific_user_document(target_user_id)
    else:
        print(f"\n❌ 指定されたドキュメント {target_user_id} が見つかりません")
        print(f"代替として最初のユーザー {user_ids[0]} を確認します")
        target_user_id = user_ids[0]
        success, user_data, conversation_fields = check_specific_user_document(target_user_id)
    
    if success and user_data:
        # callID を抽出
        call_ids = extract_call_ids_from_data(user_data, conversation_fields)
        
        if call_ids:
            # 実際の会話履歴取得をテスト
            test_conversation_retrieval_with_real_data(target_user_id, call_ids)
        else:
            print("\n❌ callID が見つかりませんでした")
    
    print("\n実際の既存会話履歴データ確認が完了しました。") 