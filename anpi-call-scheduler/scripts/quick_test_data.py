#!/usr/bin/env python3
"""
現在時刻のテストデータを作成するスクリプト
"""
import mysql.connector
from datetime import datetime, time

db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'default',
    'password': 'TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=',
    'database': 'default',
    'ssl_disabled': True
}

current_time = datetime.now()
print(f"現在時刻: {current_time.strftime('%H:%M:%S')}")

# 曜日マッピング
weekday_to_db = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
current_db_weekday = weekday_to_db[current_time.weekday()]

connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# 既存のテストデータを削除
cursor.execute("DELETE FROM users WHERE last_name LIKE 'テスト時刻%'")
print(f"既存のテストデータを削除: {cursor.rowcount}件")

# 現在時刻±2分のテストデータを作成
test_times = []
for offset in [-2, -1, 0, 1, 2]:
    hour = current_time.hour
    minute = current_time.minute + offset
    
    if minute < 0:
        hour -= 1
        minute += 60
    elif minute >= 60:
        hour += 1
        minute -= 60
    
    if hour < 0:
        hour = 23
    elif hour >= 24:
        hour = 0
        
    test_times.append(time(hour, minute, 0))

for i, test_time in enumerate(test_times):
    offset_desc = ['2分前', '1分前', '現在時刻', '1分後', '2分後'][i]
    cursor.execute("""
        INSERT INTO users (user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (f'test-current-{i+1}', f'テスト時刻{offset_desc}', '太郎', '090-1234-5678', test_time, current_db_weekday))

connection.commit()
print(f"新しいテストデータを追加: {len(test_times)}件")

# 確認
cursor.execute("SELECT last_name, call_time, call_weekday FROM users WHERE last_name LIKE 'テスト時刻%' ORDER BY call_time")
results = cursor.fetchall()
print("\n作成されたテストデータ:")
for row in results:
    print(f"  - {row[0]}: {row[1]} ({row[2]})")

connection.close()
print("データベース接続を閉じました")
