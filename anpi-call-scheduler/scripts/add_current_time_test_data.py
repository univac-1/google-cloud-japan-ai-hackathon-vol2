#!/usr/bin/env python3
"""
現在時刻に近いテストデータを追加するスクリプト
"""

import mysql.connector
from datetime import datetime, time

def add_current_time_test_data():
    """現在時刻に近いテストデータを追加"""
    
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
    print(f"現在曜日: {current_time.weekday()} (土曜日=5)")
    
    # 現在時刻の前後2分のテスト時間を生成
    test_times = [
        (current_time.hour, current_time.minute - 2),  # 2分前
        (current_time.hour, current_time.minute - 1),  # 1分前  
        (current_time.hour, current_time.minute),      # 現在時刻
        (current_time.hour, current_time.minute + 1),  # 1分後
        (current_time.hour, current_time.minute + 2),  # 2分後
    ]
    
    # 分の調整（負の値や60以上の値を正規化）
    normalized_times = []
    for hour, minute in test_times:
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
            
        normalized_times.append(time(hour, minute, 0))
    
    print("追加するテスト時間:")
    for i, test_time in enumerate(normalized_times):
        print(f"  - {test_time} ({['2分前', '1分前', '現在時刻', '1分後', '2分後'][i]})")
    
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 既存の現在時刻テストデータを削除
        cursor.execute("""
            DELETE FROM users 
            WHERE last_name = 'テスト現在時刻' 
            OR last_name LIKE 'テスト時刻%'
        """)
        print(f"既存のテストデータを削除: {cursor.rowcount}件")
        
        # 新しいテストデータを挿入
        for i, test_time in enumerate(normalized_times):
            time_label = ['2分前', '1分前', '現在時刻', '1分後', '2分後'][i]
            
            cursor.execute("""
                INSERT INTO users (
                    user_id, last_name, first_name, phone_number, 
                    call_time, call_weekday, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW()
                )
            """, (
                f'test-current-{i+1}',
                f'テスト時刻{time_label}',
                '太郎',
                '+81-90-1234-5678',
                test_time,
                'sat'  # 土曜日
            ))
        
        connection.commit()
        print(f"新しいテストデータを追加: {len(normalized_times)}件")
        
        # 追加されたデータを確認
        cursor.execute("""
            SELECT last_name, first_name, call_time, call_weekday 
            FROM users 
            WHERE last_name LIKE 'テスト時刻%'
            ORDER BY call_time
        """)
        
        results = cursor.fetchall()
        print("\n追加されたテストデータ:")
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
    add_current_time_test_data()
