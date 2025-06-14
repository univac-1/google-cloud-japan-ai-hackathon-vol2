#!/usr/bin/env python3
"""
ローカル環境でのアプリケーション動作テスト
Cloud Tasksは模擬実行（ダミー）で、データベース連携と即時実行判定をテストする
"""

import os
import sys
sys.path.append('/home/yasami/google-cloud-japan-ai-hackathon-vol2/anpi-call-scheduler/cloud-run-jobs')

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

# mainモジュールをインポート
import main

# モックでCloud Tasksの作成をテスト
class MockCloudTasksClient:
    class MockTask:
        def __init__(self, name):
            self.name = name
    
    def queue_path(self, project_id, location, queue_name):
        return f"projects/{project_id}/locations/{location}/queues/{queue_name}"
    
    def create_task(self, parent, task):
        task_name = f"{parent}/tasks/mock-task-{int(main.datetime.now().timestamp())}"
        print(f"🎭 [MOCK] Cloud Task作成: {task_name}")
        print(f"🎭 [MOCK] Payload: {task.get('http_request', {}).get('body', b'').decode()}")
        return self.MockTask(task_name)

# Cloud Tasksクライアントをモックに置き換え
original_client = main.tasks_v2.CloudTasksClient
main.tasks_v2.CloudTasksClient = MockCloudTasksClient

def test_immediate_execution():
    """即時実行機能のテスト"""
    print("🚀 即時実行機能のテスト開始")
    print("=" * 60)
    
    # 現在時刻の表示
    current_time = main.datetime.now()
    current_weekday = current_time.weekday()
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    
    print(f"📅 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} ({weekday_names[current_weekday]}曜日)")
    print()
    
    # データベースから即時実行対象ユーザーを取得
    try:
        immediate_users = main.get_immediate_call_users()
        print(f"✅ 即時実行対象ユーザー数: {len(immediate_users)}")
        
        if immediate_users:
            print("\n📞 即時実行対象ユーザー詳細:")
            for user in immediate_users:
                print(f"  - {user['last_name']} {user['first_name']}")
                print(f"    電話番号: {user['phone_number']}")
                print(f"    設定時刻: {user['call_time']} ({user['call_weekday']})")
                print()
        else:
            print("ℹ️  現在時刻では即時実行対象のユーザーはいません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cloud Tasksタスク作成のテスト
    try:
        print("\n🎭 Cloud Tasksタスク作成テスト (MOCK)")
        created_tasks = main.create_immediate_tasks()
        print(f"✅ 作成されたタスク数: {len(created_tasks)}")
        
        if created_tasks:
            print("\n📋 作成されたタスク詳細:")
            for task in created_tasks:
                print(f"  - タスク名: {task['task_name']}")
                print(f"    ユーザー: {task['user_name']}")
                print(f"    実行時刻: {task['execution_time']}")
                print()
        
    except Exception as e:
        print(f"❌ Cloud Tasksタスク作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ 即時実行機能のテストが完了しました")
    return True

def test_time_judgment():
    """時刻判定機能の詳細テスト"""
    print("\n🕐 時刻判定機能の詳細テスト")
    print("=" * 60)
    
    current_time = main.datetime.now()
    current_weekday = current_time.weekday()
    
    # 土曜日（5）をテスト
    test_cases = [
        ('sat', main.time(17, 0, 0), '17:00:00 (土曜日) - 現在時刻付近'),
        ('sat', main.time(16, 55, 0), '16:55:00 (土曜日) - 5分前'),
        ('sat', main.time(17, 5, 0), '17:05:00 (土曜日) - 5分後'),
        ('sat', main.time(17, 10, 0), '17:10:00 (土曜日) - 10分後（範囲外）'),
        ('sun', main.time(17, 0, 0), '17:00:00 (日曜日) - 曜日不一致'),
        ('mon', main.time(9, 0, 0), '09:00:00 (月曜日) - 曜日不一致'),
    ]
    
    for weekday, call_time, description in test_cases:
        should_call = main.should_call_now(weekday, call_time, 5)
        status = "✅ 実行対象" if should_call else "❌ 実行対象外"
        print(f"  {status}: {description}")
    
    print()

if __name__ == "__main__":
    print("🧪 anpi-call-scheduler ローカル動作テスト")
    print("=" * 60)
    
    # 時刻判定機能のテスト
    test_time_judgment()
    
    # 即時実行機能のテスト
    success = test_immediate_execution()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 全てのテストが正常に完了しました！")
    else:
        print("❌ テストで問題が発生しました")
    
    # Cloud Tasksクライアントを元に戻す
    main.tasks_v2.CloudTasksClient = original_client
