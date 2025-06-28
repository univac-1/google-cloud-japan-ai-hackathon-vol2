#!/usr/bin/env python3
"""
データベース接続テスト用スクリプト
"""
import os
import sys

# 環境変数を読み込み
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

# パスを追加
sys.path.append(os.path.dirname(__file__))

from get_info.db_connection import test_connection

def main():
    print("=== データベース接続テスト ===")
    print(f"DB_HOST: {os.environ.get('DB_HOST', '未設定')}")
    print(f"DB_PORT: {os.environ.get('DB_PORT', '未設定')}")
    print(f"DB_USER: {os.environ.get('DB_USER', '未設定')}")
    print(f"DB_NAME: {os.environ.get('DB_NAME', '未設定')}")
    print(f"DB_PASSWORD: {'設定あり' if os.environ.get('DB_PASSWORD') else '未設定'}")
    print()
    
    try:
        result = test_connection()
        if result:
            print("✅ データベース接続成功!")
        else:
            print("❌ データベース接続失敗")
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")

if __name__ == "__main__":
    main()
