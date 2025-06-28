#!/usr/bin/env python3
"""
Flaskアプリケーションのローカル動作テスト
"""
import os
import sys
import requests
import json
import time
from threading import Thread

def test_flask_import():
    """Flaskアプリケーションのインポートテスト"""
    print("🔄 Flaskアプリケーションのインポートテストを開始...")
    
    try:
        # main.pyのインポートテスト
        from main import app
        print("✅ main.pyのインポートが成功しました")
        return True
    except Exception as e:
        print(f"❌ main.pyのインポートでエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_diary_generation_direct():
    """DiaryGeneratorの直接テスト"""
    print("\n🔄 DiaryGenerator直接テストを開始...")
    
    try:
        from create_diary_entry.gemini_service import DiaryGenerator
        
        # テストデータ
        test_user_info = {
            "name": "田中花子",
            "last_name": "田中",
            "first_name": "花子",
            "birth_date": "1955-03-20",
            "prefecture": "神奈川県",
            "address_block": "横浜市"
        }
        
        test_conversation = {
            "conversation": [
                {"role": "assistant", "text": "こんにちは、田中さん。今日はいかがお過ごしですか？"},
                {"role": "user", "text": "こんにちは。今日は娘と一緒に買い物に行ってきました。"},
                {"role": "assistant", "text": "それは良いですね。どちらへお買い物に？"},
                {"role": "user", "text": "近所のスーパーマーケットです。夕飯の材料を買いました。"},
                {"role": "assistant", "text": "お疲れ様でした。どんなお料理を作る予定ですか？"},
                {"role": "user", "text": "今夜は肉じゃがを作る予定です。娘の好物なんです。"}
            ]
        }
        
        # DiaryGenerator実行
        generator = DiaryGenerator()
        success, diary_text, error = generator.generate_diary_entry(test_user_info, test_conversation)
        
        if success:
            print("✅ DiaryGenerator直接テスト成功!")
            print("\n📄 生成された日記:")
            print("=" * 50)
            print(diary_text)
            print("=" * 50)
            return True
        else:
            print(f"❌ DiaryGenerator直接テスト失敗: {error}")
            return False
            
    except Exception as e:
        print(f"❌ DiaryGenerator直接テストでエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_flask_server():
    """Flaskサーバーをバックグラウンドで起動"""
    try:
        from main import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Flaskサーバー起動エラー: {e}")

def test_flask_endpoints():
    """FlaskエンドポイントのHTTPテスト"""
    print("\n🔄 Flaskエンドポイントテストを開始...")
    
    # Flaskサーバーをバックグラウンドで起動
    server_thread = Thread(target=start_flask_server, daemon=True)
    server_thread.start()
    
    # サーバー起動待機
    print("⏳ Flaskサーバーの起動を待機中...")
    time.sleep(3)
    
    base_url = "http://localhost:5000"
    
    # ヘルスチェック
    try:
        print("📡 ヘルスチェック...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ ヘルスチェック成功")
            print(f"   レスポンス: {response.json()}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックでエラー: {e}")
        return False
    
    # 日記生成テスト（モックデータ）
    try:
        print("\n📡 日記生成エンドポイントテスト...")
        test_data = {
            "userID": "test_user_001",
            "callID": "test_call_001"
        }
        
        response = requests.post(
            f"{base_url}/generate-diary",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 日記生成エンドポイントテスト成功")
            result = response.json()
            print(f"   生成された日記の一部: {result.get('data', {}).get('diary', 'N/A')[:100]}...")
        else:
            print(f"❌ 日記生成エンドポイントテスト失敗: {response.status_code}")
            print(f"   エラー内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 日記生成エンドポイントテストでエラー: {e}")
        return False
    
    return True

def main():
    """メイン実行関数"""
    print("🚀 AI日記生成アプリケーション ローカル動作テスト")
    print("=" * 60)
    
    # APIキー確認
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        return False
    
    # Flaskアプリインポートテスト
    if not test_flask_import():
        return False
    
    # DiaryGenerator直接テスト
    if not test_diary_generation_direct():
        return False
    
    # Flaskエンドポイントテスト
    if not test_flask_endpoints():
        return False
    
    print("\n" + "=" * 60)
    print("🎉 すべてのテストが正常に完了しました！")
    print("✅ AI日記生成アプリケーションがローカルで正常に動作しています")
    print("📝 本格運用の準備が整いました")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
