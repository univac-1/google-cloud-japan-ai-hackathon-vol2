#!/usr/bin/env python3
"""
環境設定確認スクリプト
"""

import os
import sys

def main():
    print("=== AI Diary Service 環境確認 ===")
    print()
    
    # .envファイルの読み込み
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
    
    # 必要な環境変数の確認
    required_vars = {
        'DB_PASSWORD': 'データベースパスワード',
        'GEMINI_API_KEY': 'Gemini APIキー',
        'GOOGLE_CLOUD_PROJECT': 'Google Cloudプロジェクト',
        'DB_HOST': 'データベースホスト',
        'DB_USER': 'データベースユーザー'
    }
    
    print("📋 環境変数チェック:")
    all_ok = True
    for var, desc in required_vars.items():
        value = os.environ.get(var)
        if value:
            if var == 'GEMINI_API_KEY':
                print(f"✅ {var}: {value[:10]}...")
            elif var == 'DB_PASSWORD':
                print(f"✅ {var}: [設定済み]")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定 ({desc})")
            all_ok = False
    
    print()
    
    # Cloud SQL Proxyの確認
    print("🔍 Cloud SQL Proxy確認:")
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'cloud_sql_proxy' in result.stdout:
            print("✅ Cloud SQL Proxy は起動中です")
        else:
            print("❌ Cloud SQL Proxy が起動していません")
            print("   以下のコマンドで起動してください:")
            print("   cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306")
            all_ok = False
    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")
        all_ok = False
    
    print()
    
    if all_ok:
        print("🎉 環境設定は正常です！")
        return True
    else:
        print("⚠️ 環境設定に問題があります。上記のエラーを修正してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
