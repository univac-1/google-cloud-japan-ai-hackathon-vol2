#!/usr/bin/env python3
"""
データベーススキーマ確認とテストデータ追加
"""

import mysql.connector
import uuid
from datetime import datetime, time

def check_schema():
    """データベーススキーマを確認"""
    conn = mysql.connector.connect(
        host='127.0.0.1', port=3306, user='default', 
        password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=', 
        database='default', ssl_disabled=True
    )
    cursor = conn.cursor()
    
    # usersテーブルの構造を確認
    cursor.execute('DESCRIBE users')
    columns = cursor.fetchall()
    
    print('📋 usersテーブルの構造:')
    for column in columns:
        field, type_info, null, key, default, extra = column
        print(f'  - {field}: {type_info} (NULL: {null})')
    
    cursor.close()
    conn.close()

def add_current_time_test_data():
    """現在時刻に近いテストデータを追加"""
    current_time = datetime.now()
    print(f'\n現在時刻: {current_time.strftime("%H:%M:%S")}')
    
    # 現在時刻+/-2分のテスト時間を生成
    current_minute = current_time.minute
    current_hour = current_time.hour
    
    # テスト時間（現在時刻、1分後、2分後）
    test_times = [
        time(current_hour, current_minute, 0),
        time(current_hour, (current_minute + 1) % 60, 0),
        time(current_hour, (current_minute + 2) % 60, 0)
    ]
    
    print('\n追加するテスト時間:')
    for i, t in enumerate(test_times):
        print(f'  - {t}')
    
    # データベース接続
    conn = mysql.connector.connect(
        host='127.0.0.1', port=3306, user='default', 
        password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=', 
        database='default', ssl_disabled=True
    )
    cursor = conn.cursor()
    
    # 既存のテストデータを削除
    cursor.execute('DELETE FROM users WHERE last_name LIKE "テスト時刻%"')
    print(f'\n既存テストデータ削除: {cursor.rowcount}件')
    
    # 新しいテストデータを追加（適切な電話番号形式で）
    for i, test_time in enumerate(test_times):
        user_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO users (user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (
            user_id,
            f'テスト時刻{["現在", "1分後", "2分後"][i]}',
            '太郎',
            '090-1234-5678',  # 短い電話番号形式
            test_time,
            'sat'
        ))
    
    conn.commit()
    print(f'新テストデータ追加: {len(test_times)}件')
    
    # 追加されたデータを確認
    cursor.execute('''
        SELECT last_name, first_name, phone_number, call_time, call_weekday 
        FROM users 
        WHERE last_name LIKE "テスト時刻%" 
        ORDER BY call_time
    ''')
    users = cursor.fetchall()
    
    print('\n📋 追加されたテストユーザー:')
    for user in users:
        last_name, first_name, phone_number, call_time, call_weekday = user
        print(f'  - {last_name} {first_name}: {call_time} ({call_weekday}) {phone_number}')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        print("🔍 データベーススキーマ確認")
        check_schema()
        
        print("\n" + "="*50)
        print("📝 現在時刻テストデータ追加")
        add_current_time_test_data()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
