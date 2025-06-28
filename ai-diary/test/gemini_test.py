#!/usr/bin/env python3
"""
Gemini API 動作確認テストスクリプト
"""

import os
import sys
from typing import Optional

def check_environment() -> bool:
    """環境変数の確認"""
    print("=== Gemini API 環境確認 ===")
    
    # Gemini API キーの確認
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 環境変数が設定されていません")
        print("以下の手順でAPIキーを設定してください:")
        print("1. https://ai.google.dev/ にアクセス")
        print("2. Google AI Studio でAPIキーを取得")
        print("3. export GEMINI_API_KEY=your_api_key_here")
        return False
    else:
        print(f"✅ GEMINI_API_KEY: {'*' * (len(api_key) - 8) + api_key[-8:]}")
    
    # ライブラリの確認
    try:
        from google import genai
        print("✅ google-genai ライブラリがインストールされています")
        return True
    except ImportError:
        print("❌ google-genai ライブラリがインストールされていません")
        print("pip install google-genai を実行してください")
        return False

def test_gemini_basic() -> bool:
    """基本的なGemini API呼び出しテスト"""
    try:
        from google import genai
        
        print("\n=== Gemini API 基本テスト ===")
        
        # クライアント初期化
        client = genai.Client()
        print("✅ Gemini クライアント初期化成功")
        
        # 簡単なテキスト生成
        print("📝 テスト用プロンプト実行中...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="こんにちは、Geminiです。今日は良い天気ですね。"
        )
        
        print("✅ Gemini API呼び出し成功")
        print(f"📄 レスポンス: {response.text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini API呼び出しエラー: {str(e)}")
        return False

def test_gemini_diary_style() -> bool:
    """日記風の文章生成テスト"""
    try:
        from google import genai
        
        print("\n=== 日記風文章生成テスト ===")
        
        client = genai.Client()
        
        # サンプルユーザー情報
        sample_user_info = {
            "name": "山田太郎",
            "age": 75,
            "address": "東京都渋谷区"
        }
        
        # サンプル会話履歴
        sample_conversation = """
        AI: おはようございます、山田さん。今日はお元気ですか？
        ユーザー: おはよう。今日は孫が遊びに来る予定なんだ。
        AI: それは素晴らしいですね。何時頃いらっしゃるのですか？
        ユーザー: 午後2時頃かな。一緒に近所の公園に散歩に行く予定だよ。
        AI: お天気も良いので、きっと楽しい時間になりますね。
        ユーザー: ありがとう。久しぶりに孫と過ごせるから楽しみだ。
        """
        
        # 日記生成用プロンプト
        prompt = f"""
        以下のユーザー情報と会話履歴をもとに、家族向けの温かい日記風の文章を作成してください。

        【ユーザー情報】
        名前: {sample_user_info['name']}
        年齢: {sample_user_info['age']}歳  
        住所: {sample_user_info['address']}

        【今日の会話】
        {sample_conversation}

        【要件】
        - 家族が読んで安心できる内容
        - 温かみのある表現
        - 200文字程度
        - 敬語は使わず、親しみやすい文体
        - 「今日の{sample_user_info['name']}さん」というタイトルで始める
        """
        
        print("📝 日記風文章生成中...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        print("✅ 日記風文章生成成功")
        print("\n" + "="*50)
        print("📄 生成された日記:")
        print("="*50)
        print(response.text)
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ 日記風文章生成エラー: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    print("🤖 Gemini API 動作確認テスト開始")
    print("="*60)
    
    # 環境確認
    if not check_environment():
        print("\n❌ 環境設定が完了していません。上記の指示に従って設定してください。")
        return False
    
    # 基本テスト
    if not test_gemini_basic():
        print("\n❌ 基本的なAPI呼び出しに失敗しました。")
        return False
    
    # 日記生成テスト
    if not test_gemini_diary_style():
        print("\n❌ 日記風文章生成に失敗しました。")
        return False
    
    print("\n" + "="*60)
    print("🎉 すべてのテストが正常に完了しました！")
    print("✅ Gemini APIが正常に動作しています")
    print("📝 日記生成機能の実装準備が整いました")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 