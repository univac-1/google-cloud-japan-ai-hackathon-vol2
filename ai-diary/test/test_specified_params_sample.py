#!/usr/bin/env python3
"""
指定パラメータでのサンプルデータ日記生成テスト
userID: 4CC0CA6A-657C-4253-99FF-C19219D30AE2
callID: CA995a950a2b9f6623a5adc987d0b31131
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_diary_entry import DiaryGenerator

# 環境変数設定
os.environ["GEMINI_API_KEY"] = "AIzaSyBINVVUZhQVP3IS1ht1RBxguS9ajibSq-c"

# 指定されたテストパラメータ
USER_ID = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
CALL_ID = "CA995a950a2b9f6623a5adc987d0b31131"

def test_diary_generation_with_specified_params():
    """指定パラメータでのサンプルデータ日記生成テスト"""
    
    print(f"🚀 指定パラメータでの日記生成テスト")
    print(f"📋 userID: {USER_ID}")
    print(f"📋 callID: {CALL_ID}")
    print("=" * 60)
    
    # サンプルユーザー情報（指定userIDに基づく）
    sample_user_info = {
        "user_id": USER_ID,
        "last_name": "田中",
        "first_name": "花子",
        "age": 78,
        "phone_number": "080-1234-5678",
        "address": "東京都世田谷区",
        "emergency_contact_name": "田中太郎",
        "emergency_contact_phone": "090-8765-4321",
        "medical_conditions": "高血圧",
        "created_at": "2025-06-01T10:00:00Z"
    }
    
    # サンプル会話履歴（指定callIDに基づく）
    sample_conversation_data = {
        "call_id": CALL_ID,
        "user_id": USER_ID,
        "start_time": "2025-06-28T09:00:00Z",
        "end_time": "2025-06-28T09:05:30Z",
        "conversation": [
            {
                "timestamp": "2025-06-28T09:00:15Z",
                "speaker": "assistant",
                "message": "おはようございます、田中さん。今日の体調はいかがですか？"
            },
            {
                "timestamp": "2025-06-28T09:00:25Z",
                "speaker": "user", 
                "message": "おはよう。今日は調子がいいよ。朝から孫が遊びに来る予定で、楽しみにしているの。"
            },
            {
                "timestamp": "2025-06-28T09:01:00Z",
                "speaker": "assistant",
                "message": "それは素晴らしいですね！お孫さんとはどんなことをして過ごす予定ですか？"
            },
            {
                "timestamp": "2025-06-28T09:01:15Z",
                "speaker": "user",
                "message": "一緒に近所の公園へお散歩に行って、それから家で絵を描く約束をしているの。7歳の女の子で、とても元気なの。"
            },
            {
                "timestamp": "2025-06-28T09:02:00Z",
                "speaker": "assistant",
                "message": "お天気も良いようですし、きっと楽しい一日になりそうですね。"
            },
            {
                "timestamp": "2025-06-28T09:02:20Z",
                "speaker": "user",
                "message": "そうなの。久しぶりに会えるから、本当に嬉しくて。今から準備をしなくちゃ。"
            }
        ]
    }
    
    try:
        # DiaryGeneratorのインスタンス作成
        generator = DiaryGenerator()
        
        print("📝 サンプルデータでの日記生成を開始...")
        print()
        
        # 日記生成
        success, diary_text, error_message = generator.generate_diary_entry(
            sample_user_info, 
            sample_conversation_data
        )
        
        if success:
            print("✅ 日記生成成功！")
            print()
            print("=" * 60)
            print("📖 生成された日記:")
            print("=" * 60)
            print(diary_text)
            print("=" * 60)
            print()
            print(f"✨ テスト完了 - userID: {USER_ID}, callID: {CALL_ID}")
            
        else:
            print(f"❌ 日記生成失敗: {error_message}")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    test_diary_generation_with_specified_params()
