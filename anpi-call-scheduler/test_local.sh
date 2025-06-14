#!/bin/bash
# ローカル環境でのテスト実行スクリプト

# 環境変数を設定
export GOOGLE_CLOUD_PROJECT="univac-aiagent"
export CLOUD_TASKS_LOCATION="asia-northeast1"
export CLOUD_TASKS_QUEUE="anpi-call-queue"
export ANPI_CALL_URL="https://httpbin.org/post"
export IMMEDIATE_CALL_TOLERANCE_MINUTES="5"
export LOG_LEVEL="DEBUG"
export ENVIRONMENT="development"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_USER="default"
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="
export DB_NAME="default"
export USE_CLOUD_SQL="false"
export IS_CLOUD_RUN_JOB="false"

echo "🧪 anpi-call-scheduler ローカル動作テスト"
echo "============================================"

echo "📅 現在時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🔧 環境変数設定:"
echo "  - GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "  - IMMEDIATE_CALL_TOLERANCE_MINUTES: $IMMEDIATE_CALL_TOLERANCE_MINUTES"
echo "  - LOG_LEVEL: $LOG_LEVEL"
echo "  - DB_HOST: $DB_HOST"
echo ""

echo "🚀 データベース接続テスト"
echo "========================"
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/anpi-call-scheduler
source .venv/bin/activate

# 現在の即時実行対象ユーザーを確認
python -c "
import mysql.connector
from datetime import datetime, time

# データベース接続
conn = mysql.connector.connect(
    host='127.0.0.1', 
    port=3306, 
    user='default', 
    password='TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0=', 
    database='default', 
    ssl_disabled=True
)
cursor = conn.cursor(dictionary=True)

# 現在時刻の取得
current_time = datetime.now()
current_weekday = current_time.weekday()
weekday_names = ['月', '火', '水', '木', '金', '土', '日']

print(f'📅 現在時刻: {current_time.strftime(\"%Y-%m-%d %H:%M:%S\")} ({weekday_names[current_weekday]}曜日)')
print()

# 通話スケジュール設定のあるユーザーを取得
cursor.execute('SELECT user_id, last_name, first_name, phone_number, call_time, call_weekday FROM users WHERE call_time IS NOT NULL AND call_weekday IS NOT NULL ORDER BY call_time')
users = cursor.fetchall()

print('📋 通話スケジュール設定のあるユーザー:')
for user in users:
    print(f'  - {user[\"last_name\"]} {user[\"first_name\"]}: {user[\"call_time\"]} ({user[\"call_weekday\"]})')

print()

# 曜日マッピング
weekday_map = {
    'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2,
    'thu': 3, 'fri': 4, 'sat': 5
}

# 即時実行判定
print('🔍 即時実行判定結果:')
immediate_users = []
tolerance_minutes = 5

for user in users:
    call_weekday = user['call_weekday']
    call_time = user['call_time']
    
    # 曜日チェック
    target_weekday = weekday_map.get(call_weekday)
    if target_weekday is None or current_weekday != target_weekday:
        print(f'  ❌ {user[\"last_name\"]} {user[\"first_name\"]}: 曜日不一致 (今日:{current_weekday}, 設定:{target_weekday})')
        continue
    
    # 時刻チェック
    target_datetime = datetime.combine(current_time.date(), call_time)
    time_diff_seconds = (current_time - target_datetime).total_seconds()
    time_diff_minutes = time_diff_seconds / 60
    
    if -tolerance_minutes <= time_diff_minutes <= tolerance_minutes:
        print(f'  ✅ {user[\"last_name\"]} {user[\"first_name\"]}: 即時実行対象 (差分: {time_diff_minutes:.1f}分)')
        immediate_users.append(user)
    else:
        print(f'  ❌ {user[\"last_name\"]} {user[\"first_name\"]}: 時間外 (差分: {time_diff_minutes:.1f}分)')

print()
print(f'🎯 即時実行対象ユーザー数: {len(immediate_users)}')

cursor.close()
conn.close()
"

echo ""
echo "✅ データベース接続テスト完了"
