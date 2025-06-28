#!/usr/bin/env python3
"""
AI Diary Service サンプルデータテスト
DB接続不要でGemini API機能をテスト
"""

import os
import sys

# テスト用パラメータ
TEST_USER_ID = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
TEST_CALL_ID = "CA995a950a2b9f6623a5adc987d0b31131"

def test_diary_generation_with_sample_data():
    """サンプルデータを使用した日記生成テスト"""
    print("🔄 サンプルデータを使用した日記生成テストを開始します...")
    
    # サンプルユーザー情報
    sample_user_info = {
        "user_id": TEST_USER_ID,
        "last_name": "田中",
        "first_name": "太郎",
        "birth_date": "1945-03-15",
        "prefecture": "神奈川県",
        "address_block": "横浜市青葉区",
        "phone_number": "090-1234-5678",
        "email": "tanaka.taro@example.com"
    }
    
    # サンプル会話履歴
    sample_conversation_data = {
        "conversation": [
            {"role": "assistant", "text": "おはようございます、田中さん。今日の体調はいかがですか？"},
            {"role": "user", "text": "おはよう。今日は体調がいいよ。"},
            {"role": "assistant", "text": "それは良かったです。今日は何かご予定はありますか？"},
            {"role": "user", "text": "午後に娘が孫を連れて遊びに来るんだ。楽しみにしているよ。"},
            {"role": "assistant", "text": "素敵ですね！お孫さんはおいくつですか？"},
            {"role": "user", "text": "7歳になる女の子でね、とても元気な子なんだ。一緒にお絵描きをする約束をしているよ。"},
            {"role": "assistant", "text": "お絵描きですか。きっと楽しい時間になりますね。"},
            {"role": "user", "text": "ありがとう。久しぶりに賑やかになるから嬉しいよ。"},
            {"role": "assistant", "text": "ご家族との時間を大切にお過ごしください。何かお手伝いできることがあれば、いつでもお声かけくださいね。"},
            {"role": "user", "text": "ありがとう。また話そうね。"}
        ]
    }
    
    try:
        from create_diary_entry import DiaryGenerator
        
        generator = DiaryGenerator()
        success, diary_text, error = generator.generate_diary_entry(sample_user_info, sample_conversation_data)
        
        if success:
            print("✅ 日記生成テスト成功!")
            print("\n📄 生成された日記:")
            print("=" * 60)
            print(diary_text)
            print("=" * 60)
            return True
        else:
            print(f"❌ 日記生成テスト失敗: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 日記生成テスト中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_scenarios():
    """複数のシナリオでテスト"""
    print("\n🔄 複数シナリオテストを開始します...")
    
    scenarios = [
        {
            "name": "外出予定のある高齢者",
            "user_info": {
                "user_id": TEST_USER_ID,
                "last_name": "佐藤",
                "first_name": "花子",
                "birth_date": "1940-07-20",
                "prefecture": "東京都",
                "address_block": "世田谷区"
            },
            "conversation": {
                "conversation": [
                    {"role": "assistant", "text": "こんにちは、佐藤さん。"},
                    {"role": "user", "text": "こんにちは。今日は買い物に行ってきたわ。"},
                    {"role": "assistant", "text": "お疲れ様でした。何を買われたんですか？"},
                    {"role": "user", "text": "野菜と魚を買ってきたの。今晩は煮魚にする予定よ。"},
                    {"role": "assistant", "text": "美味しそうですね。料理をするのがお好きなんですね。"},
                    {"role": "user", "text": "ええ、料理は昔から好きなの。主人も喜んでくれるわ。"}
                ]
            }
        },
        {
            "name": "健康管理を気にする高齢者",
            "user_info": {
                "user_id": TEST_USER_ID,
                "last_name": "山田",
                "first_name": "一郎",
                "birth_date": "1950-12-05",
                "prefecture": "大阪府",
                "address_block": "大阪市中央区"
            },
            "conversation": {
                "conversation": [
                    {"role": "assistant", "text": "山田さん、今日の体調はいかがですか？"},
                    {"role": "user", "text": "今朝は散歩をしてきたよ。30分ほど歩いた。"},
                    {"role": "assistant", "text": "素晴らしいですね。散歩はどちらまで？"},
                    {"role": "user", "text": "近所の公園まで行ってきた。桜がきれいに咲いていたよ。"},
                    {"role": "assistant", "text": "春らしくて良いですね。運動を続けていらっしゃって素晴らしいです。"},
                    {"role": "user", "text": "医者からも歩くように言われているからね。継続は力なりだ。"}
                ]
            }
        }
    ]
    
    success_count = 0
    total_count = len(scenarios)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- シナリオ {i}: {scenario['name']} ---")
        try:
            from create_diary_entry import DiaryGenerator
            
            generator = DiaryGenerator()
            success, diary_text, error = generator.generate_diary_entry(
                scenario['user_info'], 
                scenario['conversation']
            )
            
            if success:
                print(f"✅ シナリオ {i} 成功!")
                print(f"📄 生成された日記（抜粋）: {diary_text[:100]}...")
                success_count += 1
            else:
                print(f"❌ シナリオ {i} 失敗: {error}")
                
        except Exception as e:
            print(f"❌ シナリオ {i} エラー: {str(e)}")
    
    print(f"\n📊 複数シナリオテスト結果: {success_count}/{total_count} 成功")
    return success_count == total_count

def main():
    """メイン関数"""
    print("🚀 AI Diary Service サンプルデータテスト")
    print("=" * 50)
    print(f"テスト対象:")
    print(f"  userID: {TEST_USER_ID}")
    print(f"  callID: {TEST_CALL_ID}")
    print("=" * 50)
    
    # 環境変数チェック
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        print("   以下のコマンドで設定してください:")
        print("   export GEMINI_API_KEY='your_api_key_here'")
        return 1
    
    test_results = []
    
    # 1. サンプルデータでの基本テスト
    test_results.append(test_diary_generation_with_sample_data())
    
    # 2. 複数シナリオテスト
    test_results.append(test_multiple_scenarios())
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー:")
    print(f"  1. サンプルデータ日記生成: {'✅' if test_results[0] else '❌'}")
    print(f"  2. 複数シナリオテスト: {'✅' if test_results[1] else '❌'}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    
    if success_count == total_count:
        print(f"\n🎉 すべてのテストが成功しました! ({success_count}/{total_count})")
        print("\n💡 注意:")
        print("   - このテストはサンプルデータを使用しています")
        print("   - 実際のDB接続は別途設定が必要です")
        print("   - 実際のユーザーデータでのテストは別のスクリプトを使用してください")
        return 0
    else:
        print(f"\n⚠️  一部のテストが失敗しました: {success_count}/{total_count} 成功")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
