#!/usr/bin/env python3
"""
Gemini API動作テスト
"""
import google.generativeai as genai

# APIキーの設定
API_KEY = "AIzaSyBINVVUZhQVP3IS1ht1RBxguS9ajibSq-c"

def test_gemini_api():
    """Gemini APIの基本動作テスト"""
    print("Gemini APIテストを開始します...")
    
    try:
        # APIキーの設定
        genai.configure(api_key=API_KEY)
        
        # モデルの初期化
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # テストプロンプト
        prompt = "こんにちは！今日はいい天気ですね。簡潔に日本語で挨拶を返してください。"
        
        print(f"プロンプト: {prompt}")
        print("Gemini APIに問い合わせ中...")
        
        # API呼び出し
        response = model.generate_content(prompt)
        
        print(f"レスポンス: {response.text}")
        print("✅ Gemini APIテストが成功しました！")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini APIテストでエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_api()
