"""
サブコレクション構造でのテストデータ作成
users/{userID}/calls/{callID} 形式
"""
import os
from google.cloud import firestore
from datetime import datetime, timezone, timedelta

def create_subcollection_test_data():
    """
    サブコレクション構造でテストデータを作成
    users/{userID}/calls/{callID} 形式
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')
        db = firestore.Client(project=project_id)
        
        print("=== サブコレクション構造でのテストデータ作成 ===")
        
        # 指定されたIDでデータを作成
        user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
        call_id = "CA995a950a2b9f6623a5adc987d0b31131"
        
        # ユーザー情報を作成
        user_data = {
            "userID": user_id,
            "name": "山田一郎",
            "age": 78,
            "gender": "男性",
            "address": {
                "prefecture": "東京都",
                "city": "新宿区",
                "detail": "西新宿1-1-1"
            },
            "phone": "03-1234-5678",
            "emergency_contact": {
                "name": "山田花子",
                "relation": "娘",
                "phone": "090-9876-5432"
            },
            "medical_info": {
                "allergies": ["ペニシリン"],
                "chronic_conditions": ["高血圧", "糖尿病"],
                "medications": ["降圧剤", "血糖降下薬"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # users/{userID} ドキュメントを作成
        user_ref = db.collection('users').document(user_id)
        user_ref.set(user_data)
        print(f"✅ ユーザー {user_id} を作成しました")
        
        # 会話履歴データを作成
        conversation_data = {
            "callID": call_id,
            "userID": user_id,
            "timestamp": datetime.now(timezone.utc),
            "call_type": "scheduled",
            "status": "completed",
            "duration_seconds": 342,
            "call_start_time": datetime.now(timezone.utc) - timedelta(minutes=6),
            "call_end_time": datetime.now(timezone.utc),
            "conversation": [
                {
                    "speaker": "AI",
                    "message": "おはようございます、山田さん。今日の体調はいかがですか？",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5, seconds=50),
                    "emotion": "neutral",
                    "intent": "greeting_health_check"
                },
                {
                    "speaker": "User",
                    "message": "おはようございます。昨夜はよく眠れました。今朝は少し肩が凝っているような感じですが、全体的には調子は良いです。",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5, seconds=35),
                    "emotion": "positive",
                    "intent": "health_status_report"
                },
                {
                    "speaker": "AI",
                    "message": "肩こりがあるとのことですね。最近、同じ姿勢を続けることが多かったでしょうか？軽いストレッチや温湿布などが効果的かもしれません。",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5, seconds=20),
                    "emotion": "concerned",
                    "intent": "health_advice"
                },
                {
                    "speaker": "User",
                    "message": "そうですね。昨日はテレビを長時間見ていました。ストレッチしてみます。ところで、来週の通院の件ですが、予約の確認をしていただけますか？",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5, seconds=5),
                    "emotion": "neutral",
                    "intent": "appointment_inquiry"
                },
                {
                    "speaker": "AI",
                    "message": "承知いたしました。来週火曜日の午後2時に田中内科クリニックでの定期検診の予約がございます。お薬手帳と保険証をお忘れなくお持ちください。",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=4, seconds=50),
                    "emotion": "helpful",
                    "intent": "appointment_confirmation"
                },
                {
                    "speaker": "User",
                    "message": "ありがとうございます。忘れないようにメモしておきます。それでは今日もよろしくお願いします。",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=4, seconds=35),
                    "emotion": "grateful",
                    "intent": "gratitude_farewell"
                }
            ],
            "ai_analysis": {
                "health_status": "良好",
                "concerns": ["肩こり"],
                "recommendations": ["軽いストレッチ", "温湿布の使用"],
                "follow_up_needed": False,
                "urgency_level": "low",
                "emotional_state": "positive",
                "key_topics": ["体調確認", "肩こり", "通院予約確認"]
            },
            "metadata": {
                "call_quality": "excellent",
                "background_noise_level": "low",
                "user_engagement": "high",
                "system_performance": "optimal",
                "language": "ja",
                "transcription_confidence": 0.95
            },
            "tags": ["health_check", "appointment", "pain_management"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # users/{userID}/calls/{callID} ドキュメントを作成
        call_ref = user_ref.collection('calls').document(call_id)
        call_ref.set(conversation_data)
        print(f"✅ 会話履歴 {call_id} を作成しました")
        
        # 追加の会話履歴データも作成（検証用）
        additional_call_data = {
            "callID": "CALL002",
            "userID": user_id,
            "timestamp": datetime.now(timezone.utc) - timedelta(hours=12),
            "call_type": "urgent",
            "status": "completed",
            "duration_seconds": 256,
            "call_start_time": datetime.now(timezone.utc) - timedelta(hours=12, minutes=4),
            "call_end_time": datetime.now(timezone.utc) - timedelta(hours=12),
            "conversation": [
                {
                    "speaker": "AI",
                    "message": "山田さん、こんばんは。緊急通話でお呼び出しでしたが、どのような状況でしょうか？",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=12, minutes=3, seconds=50),
                    "emotion": "concerned",
                    "intent": "emergency_response"
                },
                {
                    "speaker": "User",
                    "message": "すみません、転倒してしまって...大丈夫だと思うのですが、少し心配で...",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=12, minutes=3, seconds=30),
                    "emotion": "worried",
                    "intent": "emergency_report"
                }
            ],
            "ai_analysis": {
                "health_status": "要注意",
                "concerns": ["転倒", "怪我の可能性"],
                "recommendations": ["医療機関への連絡検討"],
                "follow_up_needed": True,
                "urgency_level": "medium",
                "emotional_state": "anxious"
            },
            "created_at": datetime.now(timezone.utc) - timedelta(hours=12)
        }
        
        call_ref2 = user_ref.collection('calls').document('CALL002')
        call_ref2.set(additional_call_data)
        print(f"✅ 追加会話履歴 CALL002 を作成しました")
        
        print("\n📊 作成したデータ:")
        print(f"   UserID: {user_id}")
        print(f"   Name: {user_data['name']}")
        print(f"   Primary CallID: {call_id}")
        print(f"   Additional CallID: CALL002")
        print(f"   Firestore Path: users/{user_id}/calls/{call_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストデータ作成エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("サブコレクション構造でのテストデータ作成を開始します...")
    
    success = create_subcollection_test_data()
    
    if success:
        print("\n✅ テストデータの作成が完了しました。")
    else:
        print("\n❌ テストデータの作成に失敗しました。") 