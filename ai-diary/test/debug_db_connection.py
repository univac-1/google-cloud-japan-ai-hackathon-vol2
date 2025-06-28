#!/usr/bin/env python3
"""
データベース接続の詳細テスト
"""

import os
import sys
sys.path.append('/home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary')

# 環境変数設定
os.environ["GEMINI_API_KEY"] = "AIzaSyBINVVUZhQVP3IS1ht1RBxguS9ajibSq-c"
os.environ["GOOGLE_CLOUD_PROJECT"] = "univac-aiagent"
os.environ["DB_HOST"] = "127.0.0.1"
os.environ["DB_PORT"] = "3306"
os.environ["DB_NAME"] = "default"
os.environ["DB_USER"] = "default"
os.environ["DB_PASSWORD"] = "TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="

def test_database_connection():
    """データベース接続の詳細テスト"""
    
    print("🔍 データベース接続詳細テスト")
    print("=" * 50)
    
    try:
        from get_info.db_connection import get_db_connection, test_connection
        
        print("📊 1. test_connection()の結果:")
        result = test_connection()
        print(f"   結果: {result}")
        
        print("\n📊 2. 直接接続テスト:")
        connection = get_db_connection()
        if connection:
            print("   ✅ 接続成功")
            
            # カーソルでクエリテスト
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   📋 MySQL バージョン: {version[0] if version else 'N/A'}")
            
            # ユーザーテーブルの確認
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   📋 テーブル一覧: {[table[0] for table in tables]}")
            
            # 指定ユーザーの確認
            user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
            cursor.execute("SELECT user_id, last_name, first_name FROM users WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                print(f"   ✅ ユーザー発見: ID={user_data[0]}, 名前={user_data[1]} {user_data[2]}")
            else:
                print(f"   ❌ ユーザー '{user_id}' が見つかりません")
                
                # 全ユーザー数を確認
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()
                print(f"   📊 総ユーザー数: {count[0] if count else 0}")
                
                # 最初の数件のユーザーIDを表示
                cursor.execute("SELECT user_id, last_name, first_name FROM users LIMIT 5")
                sample_users = cursor.fetchall()
                if sample_users:
                    print("   📋 サンプルユーザー:")
                    for user in sample_users:
                        print(f"      - ID={user[0]}, 名前={user[1]} {user[2]}")
            
            cursor.close()
            connection.close()
            
        else:
            print("   ❌ 接続失敗")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_connection()
