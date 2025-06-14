#!/usr/bin/env python3
"""
5分間隔でテストデータを大量追加するスクリプト
"""

import mysql.connector
from datetime import datetime, time
import uuid

def add_bulk_test_data():
    """5分間隔でテストデータを大量追加"""
    
    # データベース接続
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='default',
        password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=',
        database='default',
        ssl_disabled=True
    )
    cursor = conn.cursor()
    
    print("🚀 大量テストデータの追加開始")
    print("=" * 50)
    
    # 現在時刻から前後60分の範囲で5分間隔のテストデータを作成
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # 5分間隔の時刻リストを生成
    test_times = []
    
    # 現在時刻から前後60分（-60分～+60分）
    for hour_offset in range(-1, 2):  # -1, 0, 1時間
        target_hour = (current_hour + hour_offset) % 24
        for minute in range(0, 60, 5):  # 5分間隔
            test_times.append(time(target_hour, minute, 0))
    
    # 曜日は土曜日（sat）に固定
    weekday = 'sat'
    
    added_count = 0
    
    for i, test_time in enumerate(test_times):
        user_id = str(uuid.uuid4())
        last_name = f"テスト{i:03d}"
        first_name = f"ユーザー"
        phone_number = f"080-{1000 + i:04d}-{2000 + i:04d}"
        
        # データベースに挿入
        insert_query = """
        INSERT INTO users (
            user_id, last_name, first_name, phone_number, 
            call_time, call_weekday, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """
        
        try:
            cursor.execute(insert_query, (
                user_id, last_name, first_name, phone_number,
                test_time, weekday
            ))
            
            # 現在時刻との差分を計算
            target_datetime = datetime.combine(current_time.date(), test_time)
            time_diff_minutes = (current_time - target_datetime).total_seconds() / 60
            
            status = "✅ 即時実行対象" if -5 <= time_diff_minutes <= 5 else "❌ 時間外"
            
            print(f"  追加: {last_name} {first_name} - {test_time} (差分: {time_diff_minutes:.1f}分) {status}")
            added_count += 1
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    
    # コミット
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ 追加完了: {added_count}件のテストユーザーを追加しました")
    
    # 現在時刻での即時実行対象ユーザー数を確認
    print(f"\n📅 現在時刻: {current_time.strftime('%H:%M:%S')}")
    print("🎯 即時実行対象（±5分以内）になるユーザーが大量に追加されました")

if __name__ == "__main__":
    add_bulk_test_data()
