#!/usr/bin/env python3
"""
データベース接続テスト用スクリプト
ローカル環境でのデータベース接続と、Cloud SQL Proxyでの接続をテストします。
"""

import mysql.connector
import os
from typing import Optional, Dict, Any

def get_db_connection() -> Optional[mysql.connector.MySQLConnection]:
    """
    データベース接続を取得する
    Cloud SQL Proxy（ソケット接続）またはTCP接続を試行する
    """
    # ハードコーディングされた接続情報（動作確認用）
    db_host = '127.0.0.1'
    db_user = 'default'
    db_password = 'TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0='
    db_name = 'default'
    db_port = 3306
    
    print(f"接続情報:")
    print(f"  Host: {db_host}")
    print(f"  User: {db_user}")
    print(f"  Password: {'***' + db_password[-4:] if db_password else 'None'}")  # パスワードの最後4文字のみ表示
    print(f"  Database: {db_name}")
    print(f"  Port: {db_port}")
    
    connection = None
    
    # Cloud SQL Proxy（ソケット接続）を試行
    socket_path = f"/cloudsql/univac-aiagent:asia-northeast1:cloudsql-01"
    if os.path.exists(socket_path):
        try:
            print(f"\n🔄 Cloud SQL Proxy接続を試行中... (socket: {socket_path})")
            connection = mysql.connector.connect(
                unix_socket=socket_path,
                user=db_user,
                password=db_password,
                database=db_name
            )
            print("✅ Cloud SQL Proxy接続成功")
            return connection
        except mysql.connector.Error as e:
            print(f"❌ Cloud SQL Proxy接続失敗: {e}")
    else:
        print(f"⚠️ Cloud SQL Proxyソケットが見つかりません: {socket_path}")
    
    # TCP接続を試行
    try:
        print(f"\n🔄 TCP接続を試行中... (host: {db_host}:{db_port})")
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            auth_plugin='mysql_native_password',
            ssl_disabled=True
        )
        print("✅ TCP接続成功")
        return connection
    except mysql.connector.Error as e:
        print(f"❌ TCP接続失敗: {e}")
        
        # SSL無効化での接続を試行
        try:
            print(f"🔄 SSL無効でのTCP接続を再試行中...")
            connection = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
                ssl_disabled=True,
                autocommit=True
            )
            print("✅ SSL無効でのTCP接続成功")
            return connection
        except mysql.connector.Error as e2:
            print(f"❌ SSL無効でのTCP接続も失敗: {e2}")
    
    return None

def test_database_queries(connection: mysql.connector.MySQLConnection) -> None:
    """
    データベースクエリをテストする
    """
    cursor = connection.cursor(dictionary=True)
    
    try:
        # テーブル一覧を取得
        print("\n📋 データベース内のテーブル一覧:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  - {table_name}")
        
        # usersテーブルの構造を確認 
        print("\n🏗️ usersテーブルの構造:")
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  - {column['Field']}: {column['Type']} ({column['Null']}, {column['Key']})")
        
        # 通話スケジュール設定があるユーザーを検索
        print("\n👥 通話スケジュール設定のあるユーザー:")
        cursor.execute("""
            SELECT user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at
            FROM users 
            WHERE call_time IS NOT NULL OR call_weekday IS NOT NULL
            ORDER BY user_id
        """)
        users = cursor.fetchall()
        
        if users:
            for user in users:
                full_name = f"{user['last_name']} {user['first_name']}"
                print(f"  - ID: {user['user_id']}, 名前: {full_name}, 電話: {user['phone_number']}")
                print(f"    通話時間: {user['call_time']}, 曜日: {user['call_weekday']}")
                print(f"    作成日: {user['created_at']}")
                print()
        else:
            print("  ⚠️ 通話スケジュール設定のあるユーザーが見つかりません")
        
        # 全ユーザー数を確認
        cursor.execute("SELECT COUNT(*) as total FROM users")
        result = cursor.fetchone()
        print(f"📊 総ユーザー数: {result['total']}")
        
    except mysql.connector.Error as e:
        print(f"❌ クエリエラー: {e}")
    finally:
        cursor.close()

def main():
    """
    メイン関数
    """
    print("🚀 データベース接続テスト開始")
    print("=" * 50)
    
    # 環境変数の設定状況を確認
    env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
    print("🔧 環境変数の設定状況:")
    for var in env_vars:
        value = os.getenv(var)
        if var == 'DB_PASSWORD':
            display_value = '***' + value[-4:] if value else 'None'
        else:
            display_value = value if value else 'None'
        print(f"  {var}: {display_value}")
    
    # データベース接続テスト
    connection = get_db_connection()
    
    if connection:
        print(f"\n✅ データベース接続成功!")
        
        # 接続情報を表示
        print(f"サーバー情報: {connection.get_server_info()}")
        
        # クエリテストを実行
        test_database_queries(connection)
        
        # 接続を閉じる
        connection.close()
        print("\n🔒 データベース接続を閉じました")
    else:
        print("\n❌ データベース接続に失敗しました")
        print("解決方法:")
        print("1. Cloud SQL Proxy が起動していることを確認")
        print("2. 環境変数が正しく設定されていることを確認")
        print("3. データベースユーザーの認証情報を確認")
    
    print("\n" + "=" * 50)
    print("🏁 データベース接続テスト終了")

if __name__ == "__main__":
    main()
