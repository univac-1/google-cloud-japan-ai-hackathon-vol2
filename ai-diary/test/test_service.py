#!/usr/bin/env python3
"""
AI Diary Get Info Service テストスクリプト
"""

import os
from .db_connection import test_connection
from .user_service import get_user_info, test_get_user

def check_environment():
    """環境変数の確認"""
    print("=== 環境変数確認 ===")
    env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'GOOGLE_CLOUD_PROJECT']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'DB_PASSWORD':
            # パスワードは表示しない
            value = '***' if value != 'NOT SET' else 'NOT SET'
        print(f"{var}: {value}")
    
    # Cloud Run環境かどうかの確認
    is_cloud_run = (
        os.environ.get('K_SERVICE') is not None or
        os.environ.get('CLOUD_RUN_JOB') is not None or
        os.environ.get('K_CONFIGURATION') is not None
    )
    print(f"Cloud Run環境: {is_cloud_run}")
    print()

def main():
    """メインテスト関数"""
    print("AI Diary Get Info Service テスト開始")
    print("=" * 50)
    
    # 環境変数確認
    check_environment()
    
    # DB接続テスト
    print("=== DB接続テスト ===")
    if test_connection():
        print("✓ DB接続成功")
    else:
        print("✗ DB接続失敗")
        return
    print()
    
    # ユーザー情報取得テスト
    print("=== ユーザー情報取得テスト ===")
    test_get_user()
    print()
    
    print("テスト完了")

if __name__ == "__main__":
    main() 