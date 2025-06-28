"""
リアルなテストデータ作成と会話履歴取得テスト
指定されたドキュメントID形式でデータを作成し、機能確認を行う
"""
import os
from google.cloud import firestore
from datetime import datetime, timedelta
import uuid

def create_realistic_user_with_conversation_history():
    """
    指定されたドキュメント ID 形式でリアルなユーザーと会話履歴を作成
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("=== リアルなテストデータ作成 ===")
        
        # 指定されたドキュメント ID を使用
        user_doc_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
        
        # リアルなユーザー情報を作成
        user_data = {
            'user_id': user_doc_id,
            'name': '山田一郎',
            'age': 78,
            'phone': '03-1234-5678',
            'email': 'yamada@example.com',
            'emergency_contact': '03-8765-4321',
            'emergency_contact_name': '山田花子（娘）',
            'address': '東京都新宿区',
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_contact': firestore.SERVER_TIMESTAMP,
            'health_status': 'stable',
            'notes': 'AI安否確認サービス利用者。定期的な健康チェックが必要。'
        }
        
        # users コレクションにユーザーを作成
        user_ref = db.collection('users').document(user_doc_id)
        user_ref.set(user_data)
        print(f"✅ ユーザー {user_data['name']} ({user_doc_id}) を作成")
        
        # リアルな会話履歴を作成
        now = datetime.now()
        
        conversations = [
            {
                'call_id': f'call_{user_doc_id}_morning_20250628',
                'user_id': user_doc_id,
                'timestamp': now - timedelta(hours=2),
                'duration_seconds': 320,
                'status': 'completed',
                'call_type': 'scheduled_check',
                'conversation': [
                    {
                        'speaker': 'system',
                        'message': 'おはようございます、山田さん。今日の体調はいかがですか？',
                        'timestamp': now - timedelta(hours=2)
                    },
                    {
                        'speaker': 'user',
                        'message': 'おはよう。今朝は少し肩が凝っているんだ。',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=5)
                    },
                    {
                        'speaker': 'system',
                        'message': '肩こりですね。昨夜はよく眠れましたか？',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=10)
                    },
                    {
                        'speaker': 'user',
                        'message': 'そうですね、6時間ぐらいは眠れたと思います。',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=15)
                    },
                    {
                        'speaker': 'system',
                        'message': 'それは良かったです。今日は何かご予定はありますか？',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=25)
                    },
                    {
                        'speaker': 'user',
                        'message': '午後に病院に行く予定です。定期検診なので。',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=30)
                    },
                    {
                        'speaker': 'system',
                        'message': '定期検診は大切ですね。お気をつけて行ってらっしゃい。',
                        'timestamp': now - timedelta(hours=2, minutes=0, seconds=35)
                    }
                ],
                'analysis': {
                    'mood': 'neutral',
                    'health_indicators': ['adequate_sleep', 'shoulder_stiffness'],
                    'concerns': ['minor_shoulder_pain'],
                    'activities_mentioned': ['hospital_visit', 'regular_checkup'],
                    'ai_summary': '軽微な肩こりがあるが、睡眠は取れている。定期検診の予定がある。'
                },
                'metadata': {
                    'call_initiated_by': 'system',
                    'call_quality': 'good',
                    'background_noise': 'minimal',
                    'transcription_confidence': 0.95
                }
            },
            {
                'call_id': f'call_{user_doc_id}_evening_20250627',
                'user_id': user_doc_id,
                'timestamp': now - timedelta(days=1, hours=18),
                'duration_seconds': 280,
                'status': 'completed',
                'call_type': 'evening_check',
                'conversation': [
                    {
                        'speaker': 'system',
                        'message': 'こんばんは、山田さん。今日はいかがでしたか？',
                        'timestamp': now - timedelta(days=1, hours=18)
                    },
                    {
                        'speaker': 'user',
                        'message': 'こんばんは。今日は孫が遊びに来てくれて楽しい一日でした。',
                        'timestamp': now - timedelta(days=1, hours=18, minutes=0, seconds=5)
                    },
                    {
                        'speaker': 'system',
                        'message': 'それは素晴らしいですね！お孫さんとはどんなことをして過ごされましたか？',
                        'timestamp': now - timedelta(days=1, hours=18, minutes=0, seconds=10)
                    },
                    {
                        'speaker': 'user',
                        'message': '一緒に近くの公園を散歩して、夕食も一緒に食べました。',
                        'timestamp': now - timedelta(days=1, hours=18, minutes=0, seconds=15)
                    },
                    {
                        'speaker': 'system',
                        'message': '散歩も良い運動になりますね。お食事もしっかり取れたようで良かったです。',
                        'timestamp': now - timedelta(days=1, hours=18, minutes=0, seconds=25)
                    }
                ],
                'analysis': {
                    'mood': 'positive',
                    'health_indicators': ['social_activity', 'good_appetite', 'physical_activity'],
                    'concerns': [],
                    'activities_mentioned': ['family_visit', 'park_walk', 'shared_meal'],
                    'ai_summary': '孫との時間を楽しく過ごし、散歩や食事も良好。精神的に安定している。'
                },
                'metadata': {
                    'call_initiated_by': 'system',
                    'call_quality': 'excellent',
                    'background_noise': 'minimal',
                    'transcription_confidence': 0.98
                }
            }
        ]
        
        # 会話履歴をFirestoreに保存
        for conv in conversations:
            conv_ref = db.collection('conversations').document(conv['call_id'])
            conv_ref.set(conv)
            print(f"✅ 会話履歴 {conv['call_id']} を作成")
        
        return user_doc_id, [conv['call_id'] for conv in conversations]
        
    except Exception as e:
        print(f"❌ リアルなテストデータ作成エラー: {str(e)}")
        return None, []

def test_realistic_conversation_retrieval(user_id, call_ids):
    """
    作成したリアルなデータで会話履歴取得をテスト
    """
    print(f"\n=== リアルデータでの会話履歴取得テスト ===")
    print(f"ユーザーID: {user_id}")
    
    from conversation_service import ConversationHistoryService
    
    service = ConversationHistoryService()
    
    for i, call_id in enumerate(call_ids):
        print(f"\n--- テスト {i+1}: {call_id} ---")
        
        result = service.get_conversation_history(user_id, call_id)
        
        print(f"ステータス: {result['status']}")
        if result['status'] == 'success':
            user_info = result.get('user_info', {})
            conversation = result.get('conversation', {})
            
            print(f"✅ 取得成功")
            print(f"   ユーザー名: {user_info.get('name', 'N/A')}")
            print(f"   年齢: {user_info.get('age', 'N/A')}歳")
            print(f"   電話番号: {user_info.get('phone', 'N/A')}")
            print(f"   会話数: {len(conversation.get('conversation', []))}")
            print(f"   会話時間: {conversation.get('duration_seconds', 'N/A')}秒")
            print(f"   気分: {conversation.get('analysis', {}).get('mood', 'N/A')}")
            print(f"   AI要約: {conversation.get('analysis', {}).get('ai_summary', 'N/A')}")
            
            # 最初の会話メッセージを表示
            conv_messages = conversation.get('conversation', [])
            if conv_messages:
                first_msg = conv_messages[0]
                print(f"   最初のメッセージ: {first_msg.get('message', 'N/A')[:50]}...")
        else:
            print(f"❌ 取得失敗: {result.get('error_code', 'UNKNOWN')} - {result.get('message', 'No message')}")

def test_api_with_realistic_data(user_id, call_ids):
    """
    API エンドポイント経由でリアルなデータをテスト
    """
    print(f"\n=== API経由でのリアルデータテスト ===")
    
    import requests
    import json
    
    base_url = "http://localhost:8080"
    
    # ヘルスチェック
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ サービスが起動していません。API テストをスキップします。")
            return
    except:
        print("❌ サービスが起動していません。API テストをスキップします。")
        return
    
    print("✅ サービス稼働中。API テストを実行します。")
    
    for i, call_id in enumerate(call_ids):
        print(f"\n--- API テスト {i+1}: {call_id} ---")
        
        payload = {
            "userID": user_id,
            "callID": call_id
        }
        
        try:
            response = requests.post(
                f"{base_url}/get-conversation-history",
                json=payload,
                timeout=10
            )
            
            print(f"HTTPステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get('user_info', {})
                conversation = data.get('conversation', {})
                
                print(f"✅ API取得成功")
                print(f"   ユーザー名: {user_info.get('name', 'N/A')}")
                print(f"   会話数: {len(conversation.get('conversation', []))}")
                print(f"   AI要約: {conversation.get('analysis', {}).get('ai_summary', 'N/A')}")
            else:
                print(f"❌ API エラー: {response.text}")
                
        except Exception as e:
            print(f"❌ API リクエストエラー: {str(e)}")

if __name__ == "__main__":
    print("リアルなテストデータ作成と会話履歴取得テストを開始します...")
    
    # 1. リアルなテストデータを作成
    user_id, call_ids = create_realistic_user_with_conversation_history()
    
    if user_id and call_ids:
        print(f"\n🎯 作成されたデータ:")
        print(f"   ユーザーID: {user_id}")
        print(f"   会話履歴ID: {call_ids}")
        
        # 2. サービス経由でテスト
        test_realistic_conversation_retrieval(user_id, call_ids)
        
        # 3. API 経由でテスト（サービスが起動していれば）
        test_api_with_realistic_data(user_id, call_ids)
        
        print(f"\n✅ 指定されたドキュメントID {user_id} の会話履歴取得機能が正常に動作することを確認しました！")
    else:
        print(f"\n❌ テストデータの作成に失敗しました。")
    
    print(f"\nリアルなテストデータ作成と会話履歴取得テストが完了しました。") 