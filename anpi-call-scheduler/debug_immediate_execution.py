#!/usr/bin/env python3
"""
即時実行機能のデバッグ用スクリプト
問題を特定するための詳細な調査を行います
"""

import os
import sys
import mysql.connector
from datetime import datetime, time, timedelta

# 環境変数の設定
os.environ['DB_HOST'] = '127.0.0.1'
os.environ['DB_USER'] = 'default'
os.environ['DB_PASSWORD'] = 'TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0='
os.environ['DB_NAME'] = 'default'
os.environ['IMMEDIATE_CALL_TOLERANCE_MINUTES'] = '5'
os.environ['LOG_LEVEL'] = 'DEBUG'

# mainモジュールのインポート
sys.path.append('./cloud-run-jobs')
import main

def debug_time_judgment():
    """時刻判定のデバッグ"""
    print("🕐 時刻判定デバッグ")
    print("=" * 50)
    
    current_time = datetime.now()
    current_weekday = current_time.weekday()
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    
    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} ({weekday_names[current_weekday]}曜日)")
    print(f"現在曜日コード: {current_weekday} (0=月曜, 5=土曜, 6=日曜)")
    print()
    
    # データベースから直接ユーザー情報を取得
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='default',
        password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=',
        database='default',
        ssl_disabled=True
    )
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT user_id, last_name, first_name, call_time, call_weekday 
        FROM users 
        WHERE call_time IS NOT NULL AND call_weekday IS NOT NULL 
        ORDER BY call_time
    """)
    users = cursor.fetchall()
    
    print(f"📋 データベースから取得したユーザー数: {len(users)}")
    print()
    
    # 曜日マッピング
    weekday_map = {
        'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2,
        'thu': 3, 'fri': 4, 'sat': 5
    }
    
    tolerance_minutes = 5
    immediate_count = 0
    
    for user in users:
        print(f"👤 {user['last_name']} {user['first_name']}")
        print(f"   設定: {user['call_time']} ({user['call_weekday']})")
        
        # 曜日チェック
        target_weekday = weekday_map.get(user['call_weekday'])
        if target_weekday is None:
            print(f"   ❌ 不正な曜日指定: {user['call_weekday']}")
            continue
        
        print(f"   曜日マッピング: {user['call_weekday']} -> {target_weekday}")
        
        if current_weekday != target_weekday:
            print(f"   ❌ 曜日不一致 (現在:{current_weekday}, 設定:{target_weekday})")
            continue
        
        print(f"   ✅ 曜日一致")
        
        # 時刻チェック
        call_time = user['call_time']
        
        # timedeltaの場合、timeオブジェクトに変換
        if isinstance(call_time, timedelta):
            total_seconds = int(call_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            call_time = time(hours, minutes, seconds)
            print(f"   🔄 timedelta変換: {user['call_time']} -> {call_time}")
        
        # 指定時刻をdatetimeに変換
        target_datetime = datetime.combine(current_time.date(), call_time)
        
        # 現在時刻との差分を計算
        time_diff_seconds = (current_time - target_datetime).total_seconds()
        time_diff_minutes = time_diff_seconds / 60
        
        print(f"   時刻差分: {time_diff_minutes:.2f}分")
        print(f"   許容範囲: -{tolerance_minutes} <= {time_diff_minutes:.2f} <= {tolerance_minutes}")
        
        if -tolerance_minutes <= time_diff_minutes <= tolerance_minutes:
            print(f"   ✅ 即時実行対象")
            immediate_count += 1
        else:
            print(f"   ❌ 時間外")
        
        print()
    
    print(f"🎯 即時実行対象ユーザー数: {immediate_count}")
    
    cursor.close()
    conn.close()

def test_main_function():
    """main.pyの関数をテスト"""
    print("\n🧪 main.pyの関数テスト")
    print("=" * 50)
    
    try:
        # get_immediate_call_users()をテスト
        users = main.get_immediate_call_users()
        print(f"get_immediate_call_users()の結果: {len(users)}件")
        
        for user in users:
            print(f"  - {user['last_name']} {user['first_name']}: {user['call_time']} ({user['call_weekday']})")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 即時実行機能デバッグ開始")
    print("=" * 60)
    
    debug_time_judgment()
    test_main_function()
    
    print("\n✅ デバッグ完了")
