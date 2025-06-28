#!/usr/bin/env python3
"""
データベースなしでのGemini日記生成テスト
"""
import os
import sys
import requests
import json
from datetime import datetime

def test_diary_generation_api():
    """API経由での日記生成テスト（モックデータ使用）"""
    print("🔄 API経由日記生成テスト（モックデータ）を開始...")
    
    # テスト用のFlaskアプリを起動
    from flask import Flask, request, jsonify
    from create_diary_entry.gemini_service import DiaryGenerator
    
    test_app = Flask(__name__)
    
    @test_app.route('/test-diary-generation', methods=['POST'])
    def test_diary_generation():
        """テスト用日記生成エンドポイント"""
        try:
            data = request.get_json()
            
            # モックユーザー情報
            mock_user_info = {
                "name": data.get("user_name", "テストユーザー"),
                "birth_date": "1960-05-10",
                "prefecture": "東京都",
                "address_block": "港区"
            }
            
            # モック会話履歴
            mock_conversation = {
                "conversation": [
                    {"role": "assistant", "text": "こんにちは！今日はいかがお過ごしですか？"},
                    {"role": "user", "text": data.get("user_message", "今日は散歩をしました。天気が良くて気持ちよかったです。")},
                    {"role": "assistant", "text": "それは素晴らしいですね！お天気の良い日の散歩は気持ちがいいですよね。"},
                    {"role": "user", "text": "ありがとう。また明日も頑張ります。"}
                ]
            }
            
            # 日記生成
            generator = DiaryGenerator()
            success, diary_text, error = generator.generate_diary_entry(
                mock_user_info, mock_conversation
            )
            
            if success:
                return jsonify({
                    "status": "success",
                    "data": {
                        "user_info": mock_user_info,
                        "conversation": mock_conversation,
                        "diary": diary_text
                    }
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"日記生成エラー: {error}"
                }), 500
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"処理エラー: {str(e)}"
            }), 500
    
    print("✅ テスト用Flaskアプリを設定しました")
    return test_app

def run_standalone_test():
    """スタンドアロンテスト実行"""
    print("🚀 Gemini日記生成 スタンドアロンテスト")
    print("=" * 60)
    
    # APIキー確認
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        return False
    
    try:
        from create_diary_entry.gemini_service import DiaryGenerator
        
        print("🔄 日記生成テスト開始...")
        
        # テストシナリオ1: 通常の会話
        test_scenarios = [
            {
                "name": "健康的な一日",
                "user_info": {
                    "name": "佐藤太郎",
                    "birth_date": "1950-12-25",
                    "prefecture": "福岡県",
                    "address_block": "博多区"
                },
                "conversation": {
                    "conversation": [
                        {"role": "assistant", "text": "おはようございます、佐藤さん。今日はどんな一日でしたか？"},
                        {"role": "user", "text": "おはよう。今日は朝から医者に行ってきたよ。"},
                        {"role": "assistant", "text": "お疲れ様でした。検診でしょうか？"},
                        {"role": "user", "text": "そう、定期検診でね。おかげさまで健康だって言われたよ。"},
                        {"role": "assistant", "text": "それは良かったですね！安心されたでしょう。"},
                        {"role": "user", "text": "ありがとう。午後は庭仕事もしたんだ。花がきれいに咲いているよ。"}
                    ]
                }
            },
            {
                "name": "家族との時間",
                "user_info": {
                    "name": "鈴木花子",
                    "birth_date": "1955-07-03",
                    "prefecture": "北海道",
                    "address_block": "札幌市"
                },
                "conversation": {
                    "conversation": [
                        {"role": "assistant", "text": "こんにちは、鈴木さん。今日はお元気ですか？"},
                        {"role": "user", "text": "こんにちは。今日は息子家族が遊びに来てくれました。"},
                        {"role": "assistant", "text": "それは嬉しいですね！お孫さんもいらっしゃったのですか？"},
                        {"role": "user", "text": "はい、6歳の孫と一緒におやつを作りました。"},
                        {"role": "assistant", "text": "素敵な時間でしたね。どんなおやつを作られたのですか？"},
                        {"role": "user", "text": "ホットケーキです。孫がとても喜んでくれました。"}
                    ]
                }
            }
        ]
        
        generator = DiaryGenerator()
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 テストシナリオ {i}: {scenario['name']}")
            print("-" * 40)
            
            success, diary_text, error = generator.generate_diary_entry(
                scenario['user_info'], scenario['conversation']
            )
            
            if success:
                print("✅ 日記生成成功!")
                print(f"📄 生成された日記:")
                print("=" * 50)
                print(diary_text)
                print("=" * 50)
            else:
                print(f"❌ 日記生成失敗: {error}")
                return False
        
        print("\n🎉 すべてのテストシナリオが正常に完了しました！")
        print("✅ Gemini APIを使った日記生成機能が正常に動作しています")
        print("📝 家族向けの温かい日記が生成されています")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_standalone_test()
    sys.exit(0 if success else 1)
