#!/usr/bin/env python3
"""
即時実行機能の動作確認テスト
"""

import os
import sys

# 環境変数の設定（ローカルテスト用）
os.environ['GOOGLE_CLOUD_PROJECT'] = 'univac-aiagent'
os.environ['CLOUD_TASKS_LOCATION'] = 'asia-northeast1'
os.environ['CLOUD_TASKS_QUEUE'] = 'anpi-call-queue'
os.environ['ANPI_CALL_URL'] = 'https://httpbin.org/post'
os.environ['IMMEDIATE_CALL_TOLERANCE_MINUTES'] = '5'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['ENVIRONMENT'] = 'development'
os.environ['DB_HOST'] = '127.0.0.1'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'default'
os.environ['DB_PASSWORD'] = 'TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0='
os.environ['DB_NAME'] = 'default'
os.environ['USE_CLOUD_SQL'] = 'false'
os.environ['IS_CLOUD_RUN_JOB'] = 'false'

# パスの追加
sys.path.append('/home/yasami/google-cloud-japan-ai-hackathon-vol2/anpi-call-scheduler/cloud-run-jobs')

try:
    print("🚀 即時実行機能テスト開始")
    print("=" * 50)
    
    # メインモジュールをインポート
    import main
    from datetime import datetime, time
    
    # 現在時刻の表示
    current_time = datetime.now()
    print(f"📅 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 現在曜日: {current_time.weekday()} (土曜日=5)")
    print()
    
    # 即時実行判定のテスト
    print("🕐 即時実行判定テスト:")
    
    # テストケース: 土曜日 17:00 (現在時刻に近い)
    should_call_17_00 = main.should_call_now('sat', time(17, 0, 0), 5)
    print(f"  土曜日 17:00: {'✅ 実行対象' if should_call_17_00 else '❌ 実行対象外'}")
    
    # テストケース: 土曜日 16:55 (5分前)
    should_call_16_55 = main.should_call_now('sat', time(16, 55, 0), 5)
    print(f"  土曜日 16:55: {'✅ 実行対象' if should_call_16_55 else '❌ 実行対象外'}")
    
    # テストケース: 土曜日 17:05 (5分後)
    should_call_17_05 = main.should_call_now('sat', time(17, 5, 0), 5)
    print(f"  土曜日 17:05: {'✅ 実行対象' if should_call_17_05 else '❌ 実行対象外'}")
    
    # テストケース: 土曜日 17:10 (10分後、範囲外)
    should_call_17_10 = main.should_call_now('sat', time(17, 10, 0), 5)
    print(f"  土曜日 17:10: {'✅ 実行対象' if should_call_17_10 else '❌ 実行対象外'}")
    
    # テストケース: 日曜日 17:00 (曜日不一致)
    should_call_sun = main.should_call_now('sun', time(17, 0, 0), 5)
    print(f"  日曜日 17:00: {'✅ 実行対象' if should_call_sun else '❌ 実行対象外'}")
    
    print()
    
    # データベースから即時実行対象ユーザーを取得
    print("👥 データベースから即時実行対象ユーザーを取得:")
    immediate_users = main.get_immediate_call_users()
    print(f"取得したユーザー数: {len(immediate_users)}")
    
    if immediate_users:
        print("\n📞 即時実行対象ユーザー:")
        for user in immediate_users:
            print(f"  - {user['last_name']} {user['first_name']}")
            print(f"    電話番号: {user['phone_number']}")
            print(f"    設定: {user['call_time']} ({user['call_weekday']})")
            print()
    else:
        print("ℹ️  現在時刻では即時実行対象のユーザーはいません")
    
    print("✅ 即時実行機能テスト完了")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
