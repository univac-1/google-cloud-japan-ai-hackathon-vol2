#!/usr/bin/env python3
"""
現在時刻に合わせてテストデータを更新するスクリプト
"""

import mysql.connector
from datetime import datetime, time

def update_test_data_to_current_time():
    """テストデータを現在時刻に更新"""
    
    # データベース接続情報
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
    print(f"現在曜日: {current_time.weekday()} (Python weekday: 0=月曜日, 6=日曜日)")
    
    # 曜日マッピング
    weekday_to_db = {
        0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
        4: 'fri', 5: 'sat', 6: 'sun'
    }
    
    current_db_weekday = weekday_to_db[current_time.weekday()]
    print(f"データベース用曜日: {current_db_weekday}")
    
    # 現在時刻の前後のテスト時間を生成
    test_times = []
    for offset in [-2, -1, 0, 1, 2]:  # 2分前から2分後まで
        hour = current_time.hour
        minute = current_time.minute + offset
        
        # 分の調整
        if minute < 0:
            hour -= 1
            minute += 60
        elif minute >= 60:
            hour += 1
            minute -= 60
        
        # 時の調整
        if hour < 0:
            hour = 23
        elif hour >= 24:
            hour = 0
            
        test_times.append(time(hour, minute, 0))
    
    print("\n更新するテスト時間:")
    for i, test_time in enumerate(test_times):
        offset_desc = ['2分前', '1分前', '現在時刻', '1分後', '2分後'][i]
        print(f"  - {test_time} ({offset_desc})")
    
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 既存のテストデータを削除
        cursor.execute("""
            DELETE FROM users 
            WHERE last_name LIKE 'テスト時刻%'
        """)
        print(f"\n既存のテストデータを削除: {cursor.rowcount}件")
        
        # 新しいテストデータを挿入
        for i, test_time in enumerate(test_times):
            offset_desc = ['2分前', '1分前', '現在時刻', '1分後', '2分後'][i]
            
            cursor.execute("""
                INSERT INTO users (
                    user_id, last_name, first_name, phone_number, 
                    call_time, call_weekday, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW()
                )
            """, (
                f'test-current-{i+1}',
                f'テスト時刻{offset_desc}',
                '太郎',
                '090-1234-5678',
                test_time,
                current_db_weekday
            ))
        
        connection.commit()
        print(f"新しいテストデータを追加: {len(test_times)}件")
        
        # 追加されたデータを確認
        cursor.execute("""
            SELECT last_name, first_name, call_time, call_weekday 
            FROM users 
            WHERE last_name LIKE 'テスト時刻%'
            ORDER BY call_time
        """)
        
        results = cursor.fetchall()
        print("\n更新されたテストデータ:")
        for row in results:
            print(f"  - {row[0]} {row[1]}: {row[2]} ({row[3]})")
        
    except mysql.connector.Error as e:
        print(f"データベースエラー: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nデータベース接続を閉じました")

if __name__ == "__main__":
    update_test_data_to_current_time()
