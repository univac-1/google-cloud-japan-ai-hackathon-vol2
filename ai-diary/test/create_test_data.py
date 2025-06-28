"""
会話履歴取得機能のテストデータ作成スクリプト
"""
import os
from google.cloud import firestore
from datetime import datetime, timedelta
import uuid

def create_test_users():
    """
    テストユーザーを作成
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("=== テストユーザー作成 ===")
        
        # テストユーザー情報
        test_users = [
            {
                'user_id': 'user001',
                'name': '田中太郎',
                'age': 75,
                'phone': '090-1234-5678',
                'emergency_contact': '090-8765-4321',
                'created_at': firestore.SERVER_TIMESTAMP
            },
            {
                'user_id': 'user002', 
                'name': '佐藤花子',
                'age': 82,
                'phone': '090-2345-6789',
                'emergency_contact': '090-7654-3210',
                'created_at': firestore.SERVER_TIMESTAMP
            }
        ]
        
        for user_data in test_users:
            user_ref = db.collection('users').document(user_data['user_id'])
            user_ref.set(user_data)
            print(f"✅ ユーザー {user_data['name']} ({user_data['user_id']}) を作成")
        
        return True
        
    except Exception as e:
        print(f"❌ テストユーザー作成エラー: {str(e)}")
        return False

def create_test_conversations():
    """
    テスト会話履歴を作成
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("\n=== テスト会話履歴作成 ===")
        
        # 現在時刻から過去の会話を生成
        now = datetime.now()
        
        # ユーザー001の会話履歴
        conversations_user001 = [
            {
                'call_id': 'call_001_20241201_morning',
                'user_id': 'user001',
                'timestamp': now - timedelta(days=2, hours=8),
                'duration_seconds': 180,
                'status': 'completed',
                'conversation': [
                    {
                        'speaker': 'system',
                        'message': 'おはようございます、田中さん。今日の体調はいかがですか？',
                        'timestamp': now - timedelta(days=2, hours=8)
                    },
                    {
                        'speaker': 'user',
                        'message': 'おはよう。昨日の夜はよく眠れたよ。',
                        'timestamp': now - timedelta(days=2, hours=8, minutes=0, seconds=5)
                    },
                    {
                        'speaker': 'system',
                        'message': 'それは良かったです。今日の予定はありますか？',
                        'timestamp': now - timedelta(days=2, hours=8, minutes=0, seconds=10)
                    },
                    {
                        'speaker': 'user',
                        'message': '散歩に行こうと思っているんだ。',
                        'timestamp': now - timedelta(days=2, hours=8, minutes=0, seconds=15)
                    }
                ],
                'analysis': {
                    'mood': 'positive',
                    'health_indicators': ['good_sleep', 'active_plan'],
                    'concerns': []
                }
            },
            {
                'call_id': 'call_001_20241201_evening',
                'user_id': 'user001',
                'timestamp': now - timedelta(days=2, hours=18),
                'duration_seconds': 210,
                'status': 'completed',
                'conversation': [
                    {
                        'speaker': 'system',
                        'message': 'こんばんは、田中さん。今日はいかがでしたか？',
                        'timestamp': now - timedelta(days=2, hours=18)
                    },
                    {
                        'speaker': 'user',
                        'message': '散歩は気持ちよかったよ。夕食も美味しく食べられた。',
                        'timestamp': now - timedelta(days=2, hours=18, minutes=0, seconds=5)
                    }
                ],
                'analysis': {
                    'mood': 'positive',
                    'health_indicators': ['good_appetite', 'exercise_completed'],
                    'concerns': []
                }
            }
        ]
        
        # ユーザー002の会話履歴
        conversations_user002 = [
            {
                'call_id': 'call_002_20241201_morning',
                'user_id': 'user002',
                'timestamp': now - timedelta(days=1, hours=9),
                'duration_seconds': 150,
                'status': 'completed',
                'conversation': [
                    {
                        'speaker': 'system',
                        'message': 'おはようございます、佐藤さん。お元気ですか？',
                        'timestamp': now - timedelta(days=1, hours=9)
                    },
                    {
                        'speaker': 'user',
                        'message': 'おはよう。少し膝が痛いの。',
                        'timestamp': now - timedelta(days=1, hours=9, minutes=0, seconds=5)
                    },
                    {
                        'speaker': 'system',
                        'message': '膝の痛みですね。痛みの程度はいかがですか？',
                        'timestamp': now - timedelta(days=1, hours=9, minutes=0, seconds=10)
                    }
                ],
                'analysis': {
                    'mood': 'neutral',
                    'health_indicators': [],
                    'concerns': ['knee_pain']
                }
            }
        ]
        
        # 会話履歴をFirestoreに保存
        all_conversations = conversations_user001 + conversations_user002
        
        for conv in all_conversations:
            conv_ref = db.collection('conversations').document(conv['call_id'])
            conv_ref.set(conv)
            print(f"✅ 会話履歴 {conv['call_id']} を作成")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト会話履歴作成エラー: {str(e)}")
        return False

def verify_test_data():
    """
    作成したテストデータを確認
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("\n=== テストデータ確認 ===")
        
        # ユーザー数確認
        users_ref = db.collection('users')
        users_count = len(users_ref.get())
        print(f"📊 ユーザー数: {users_count}")
        
        # 会話履歴数確認
        conversations_ref = db.collection('conversations')
        conversations_count = len(conversations_ref.get())
        print(f"📊 会話履歴数: {conversations_count}")
        
        # サンプル会話履歴表示
        if conversations_count > 0:
            sample_conv = conversations_ref.limit(1).get()[0]
            conv_data = sample_conv.to_dict()
            print(f"\n📝 サンプル会話履歴:")
            print(f"  CallID: {conv_data.get('call_id')}")
            print(f"  ユーザーID: {conv_data.get('user_id')}")
            print(f"  会話数: {len(conv_data.get('conversation', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストデータ確認エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("テストデータ作成を開始します...")
    
    # テストユーザー作成
    if create_test_users():
        # テスト会話履歴作成
        if create_test_conversations():
            # データ確認
            verify_test_data()
    
    print("\nテストデータ作成が完了しました。") 