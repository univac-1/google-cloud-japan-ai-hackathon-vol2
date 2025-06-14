#!/usr/bin/env python3
"""
テストデータ追加スクリプト
即時実行のテストのために、現在時刻に近い通話スケジュールを持つユーザーを追加します。
"""

import mysql.connector
import uuid
from datetime import datetime, time

def get_db_connection():
    """データベース接続を取得"""
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='default',
        password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=',
        database='default',
        auth_plugin='mysql_native_password',
        ssl_disabled=True
    )

def add_test_users():
    """テスト用ユーザーを追加"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # 現在時刻を取得
    now = datetime.now()
    current_time = now.time()
    current_weekday = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][now.weekday()]
    
    print(f"現在時刻: {current_time}")
    print(f"現在曜日: {current_weekday}")
    
    # テスト用ユーザーデータ
    test_users = [
        {
            'last_name': 'テスト',
            'first_name': '即時実行',
            'phone_number': '080-1111-1111',
            'call_time': time(17, 0),  # 17:00
            'call_weekday': 'sat'  # 土曜日
        },
        {
            'last_name': 'テスト',
            'first_name': '現在時刻',
            'phone_number': '080-2222-2222',
            'call_time': time(16, 59),  # 16:59
            'call_weekday': current_weekday
        },
        {
            'last_name': 'テスト',
            'first_name': '許容時間内',
            'phone_number': '080-3333-3333',
            'call_time': time(16, 55),  # 16:55（許容時間内）
            'call_weekday': current_weekday
        }
    ]
    
    insert_query = """
    INSERT INTO users (
        user_id, last_name, first_name, phone_number, 
        call_time, call_weekday, created_at, updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    for user in test_users:
        user_id = str(uuid.uuid4())
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        
        values = (
            user_id,
            user['last_name'],
            user['first_name'],
            user['phone_number'],
            user['call_time'],
            user['call_weekday'],
            now_str,
            now_str
        )
        
        try:
            cursor.execute(insert_query, values)
            print(f"✅ 追加成功: {user['last_name']} {user['first_name']} (通話時刻: {user['call_time']}, 曜日: {user['call_weekday']})")
        except mysql.connector.Error as e:
            print(f"❌ 追加失敗: {user['last_name']} {user['first_name']} - {e}")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print(f"\n📊 テストユーザー追加完了")

def verify_test_users():
    """追加したテストユーザーを確認"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT user_id, last_name, first_name, phone_number, call_time, call_weekday
        FROM users 
        WHERE last_name = 'テスト'
        ORDER BY first_name
    """)
    
    users = cursor.fetchall()
    print(f"\n📋 追加されたテストユーザー: {len(users)}名")
    for user in users:
        print(f"  - {user['last_name']} {user['first_name']}: {user['call_time']} ({user['call_weekday']})")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    try:
        print("🚀 テストデータ追加スクリプト開始")
        add_test_users()
        verify_test_users()
        print("🏁 テストデータ追加完了")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
