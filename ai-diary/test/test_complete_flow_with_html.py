#!/usr/bin/env python3
"""
HTML生成を含む完全な日記生成フローのテスト
"""

import os
import sys
import requests
import json
from typing import Dict, Any

def load_env_file():
    """環境変数を.envファイルから読み込み"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def test_complete_diary_generation():
    """完全な日記生成フローのテスト"""
    
    # テスト用固定パラメータ
    user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    call_id = "CA995a950a2b9f6623a5adc987d0b31131"
    base_url = "http://localhost:8080"
    
    print("=== HTML生成を含む完全な日記生成フローのテスト ===")
    print(f"ユーザーID: {user_id}")
    print(f"コールID: {call_id}")
    print(f"ベースURL: {base_url}")
    print()
    
    try:
        # 1. ヘルスチェック
        print("1. ヘルスチェック")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ ヘルスチェック成功")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
        print()
        
        # 2. HTML生成API単体テスト
        print("2. HTML生成API単体テスト")
        response = requests.get(f"{base_url}/test-html", timeout=30)
        if response.status_code == 200:
            print("✅ HTML生成API接続成功")
        else:
            print(f"❌ HTML生成API接続失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
        print()
        
        # 3. 完全な日記生成
        print("3. 完全な日記生成（ユーザー情報→会話履歴→日記→挿絵→HTML）")
        payload = {
            "userID": user_id,
            "callID": call_id
        }
        
        response = requests.post(
            f"{base_url}/generate-diary",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 完全な日記生成成功")
            
            data = result.get("data", {})
            print(f"  - ユーザー情報: {'取得済み' if data.get('userInfo') else '取得失敗'}")
            print(f"  - 会話履歴: {'取得済み' if data.get('conversationHistory') else '取得失敗'}")
            print(f"  - 日記生成: {'成功' if data.get('diary') else '失敗'}")
            print(f"  - 挿絵生成: {'成功' if data.get('illustrationUrl') else '失敗'}")
            print(f"  - HTML生成: {'成功' if data.get('htmlContent') else '失敗'}")
            
            # 結果の詳細表示
            if data.get('diary'):
                print(f"\n📝 生成された日記（最初の200文字）:")
                diary_preview = data['diary'][:200] + "..." if len(data['diary']) > 200 else data['diary']
                print(diary_preview)
            
            if data.get('illustrationUrl'):
                print(f"\n🖼️ 挿絵URL: {data['illustrationUrl']}")
            
            if data.get('htmlContent'):
                html_length = len(data['htmlContent'])
                print(f"\n🌐 HTML生成成功 (長さ: {html_length}文字)")
                # HTMLの最初の100文字を表示
                html_preview = data['htmlContent'][:100] + "..." if html_length > 100 else data['htmlContent']
                print(f"HTMLプレビュー: {html_preview}")
            
            return True
        else:
            print(f"❌ 完全な日記生成失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ APIサーバーに接続できません。サーバーが起動しているか確認してください。")
        return False
    except requests.exceptions.Timeout:
        print("❌ リクエストがタイムアウトしました。")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

def main():
    """メイン関数"""
    # 環境変数読み込み
    load_env_file()
    
    # テスト実行
    success = test_complete_diary_generation()
    
    print()
    if success:
        print("🎉 テスト完了: HTML生成を含む完全な日記生成フローが正常に動作しています")
        sys.exit(0)
    else:
        print("💥 テスト失敗: エラーが発生しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
