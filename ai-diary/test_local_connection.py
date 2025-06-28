#!/usr/bin/env python3
"""
ローカル環境でのデータベース接続テスト
"""
import os

# 環境変数を設定
os.environ['DB_USER'] = 'default'
os.environ['DB_PASSWORD'] = 'TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0='
os.environ['DB_NAME'] = 'default'
os.environ['DB_HOST'] = '127.0.0.1'
os.environ['DB_PORT'] = '3306'

from get_info.db_connection import test_connection

print("🔍 ローカル環境でのDB接続テスト")
print("==================================================")

try:
    result = test_connection()
    print(f"✅ テスト結果: {result}")
    if result:
        print("✅ ローカル接続成功！")
    else:
        print("❌ ローカル接続失敗")
except Exception as e:
    print(f"❌ エラー発生: {e}")
