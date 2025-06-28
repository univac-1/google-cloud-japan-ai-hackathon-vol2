#!/usr/bin/env python3
"""
環境変数読み込みと各種接続テストスクリプト
"""

import os
import sys

def load_env_file():
    """
    .envファイルから環境変数を読み込む
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    print(f"env_path: {env_path}")
    print(f"exists: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f'Set {key}')
    else:
        print("❌ .envファイルが見つかりません")

def test_env_vars():
    """
    重要な環境変数の確認
    """
    print("\n=== 環境変数確認 ===")
    important_vars = [
        'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME',
        'GEMINI_API_KEY', 'PROJECT_ID', 'GOOGLE_CLOUD_PROJECT'
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var or 'KEY' in var:
                print(f"{var}: {'*' * len(value[:4])}...設定済み")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: ❌ 未設定")

def test_db_connection():
    """
    データベース接続テスト
    """
    print("\n=== データベース接続テスト ===")
    try:
        from get_info.db_connection import test_connection
        result = test_connection()
        print(f"DB接続テスト: {'✅ 成功' if result else '❌ 失敗'}")
        return result
    except Exception as e:
        print(f"DB接続テストエラー: {e}")
        return False

def test_gemini_api():
    """
    Gemini API接続テスト
    """
    print("\n=== Gemini API接続テスト ===")
    try:
        from create_diary_entry import DiaryGenerator
        generator = DiaryGenerator()
        result = generator.test_generation()
        print(f"Gemini API接続テスト: {'✅ 成功' if result else '❌ 失敗'}")
        return result
    except ValueError as e:
        print(f"Gemini APIキー設定エラー: {e}")
        return False
    except Exception as e:
        print(f"Gemini API接続テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("=== AI Diary Service 動作環境チェック ===")
    
    # 環境変数読み込み
    load_env_file()
    
    # 環境変数確認
    test_env_vars()
    
    # DB接続テスト
    db_ok = test_db_connection()
    
    # Gemini API テスト
    gemini_ok = test_gemini_api()
    
    print("\n=== 総合結果 ===")
    print(f"データベース接続: {'✅' if db_ok else '❌'}")
    print(f"Gemini API接続: {'✅' if gemini_ok else '❌'}")
    
    if db_ok and gemini_ok:
        print("✅ すべての事前チェックが完了しました。一連の処理テストを実行できます。")
        sys.exit(0)
    else:
        print("❌ 一部のチェックに失敗しました。設定を確認してください。")
        sys.exit(1)
