#!/usr/bin/env python3
"""
Gemini API ローカルテストスクリプト
"""

import os
import sys
sys.path.append('/home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary')

from create_diary_entry import DiaryGenerator

def test_gemini_connection():
    """Gemini API接続テスト"""
    print("🔄 Gemini API接続テストを開始します...")
    
    # APIキーを環境変数から取得
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        print("   以下のコマンドで設定してください:")
        print("   export GEMINI_API_KEY='your_api_key_here'")
        return False
    
    try:
        # DiaryGeneratorインスタンス作成
        generator = DiaryGenerator(api_key)
        
        # 接続テスト
        if generator.test_generation():
            print("✅ Gemini API接続テスト成功!")
            return True
        else:
            print("❌ Gemini API接続テスト失敗")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {str(e)}")
        return False

def test_diary_generation():
    """日記生成テスト"""
    print("\n🔄 日記生成テストを開始します...")
    
    # テストデータ
    test_user_info = {
        "name": "山田太郎",
        "last_name": "山田",
        "first_name": "太郎",
        "birth_date": "1950-04-15",
        "prefecture": "東京都",
        "address_block": "渋谷区"
    }
    
    test_conversation = {
        "conversation": [
            {"role": "assistant", "text": "おはようございます、山田さん。今日の調子はいかがですか？"},
            {"role": "user", "text": "おはよう。今日は孫が遊びに来るんだ。"},
            {"role": "assistant", "text": "それは楽しみですね！どなたのお孫さんですか？"},
            {"role": "user", "text": "息子の子供でね、5歳になる男の子なんだ。一緒に公園に行く予定だよ。"},
            {"role": "assistant", "text": "お天気も良いですし、きっと楽しい時間を過ごせますね。"},
            {"role": "user", "text": "ありがとう。久しぶりに会えるから楽しみだよ。"}
        ]
    }
    
    try:
        generator = DiaryGenerator()
        success, diary, error = generator.generate_diary_entry(test_user_info, test_conversation)
        
        if success:
            print("✅ 日記生成テスト成功!")
            print("\n📄 生成された日記:")
            print("=" * 50)
            print(diary)
            print("=" * 50)
            return True
        else:
            print(f"❌ 日記生成テスト失敗: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 日記生成テスト中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("🚀 Gemini API日記生成ローカルテスト")
    print("=" * 40)
    
    # 接続テスト
    if not test_gemini_connection():
        return 1
    
    # 日記生成テスト
    if not test_diary_generation():
        return 1
    
    print("\n🎉 すべてのテストが正常に完了しました!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
