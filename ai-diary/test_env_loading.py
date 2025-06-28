#!/usr/bin/env python3
"""
環境変数読み込みテスト用スクリプト
"""
import os

def test_env_loading():
    """環境変数の読み込みをテストする"""
    print("=== 環境変数読み込みテスト ===")
    
    # 現在のディレクトリ確認
    current_dir = os.getcwd()
    print(f"現在のディレクトリ: {current_dir}")
    
    # .envファイルのパス
    env_path = os.path.join(current_dir, '.env')
    print(f".envファイルパス: {env_path}")
    print(f".envファイル存在: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        print("\n=== .envファイル内容 ===")
        with open(env_path, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                print(f"{i:2d}: {line}")
        
        print("\n=== 環境変数読み込み ===")
        count = 0
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"✅ {key}={value[:20]}{'...' if len(value) > 20 else ''}")
                    count += 1
        
        print(f"\n読み込んだ環境変数数: {count}")
    
    # 重要な環境変数の確認
    print("\n=== 重要な環境変数確認 ===")
    important_vars = [
        'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME', 'DB_PASSWORD',
        'PROJECT_ID', 'GEMINI_API_KEY'
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            display_value = value[:10] + '...' if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: 設定なし")

if __name__ == "__main__":
    test_env_loading()
