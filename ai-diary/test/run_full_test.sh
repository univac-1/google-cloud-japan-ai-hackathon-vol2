#!/bin/bash

# AI Diary Get Info Service - 完全テストスクリプト
# サービス起動からAPIテストまで一括実行

set -e

echo "=== AI Diary Get Info Service 完全テスト開始 ==="

# 1. 設定読み込み
echo "1. 設定ファイル読み込み中..."
if [[ -f "config.env" ]]; then
    source config.env
else
    echo "config.envファイルが見つかりません"
    exit 1
fi

# 2. 環境変数設定
echo "2. 環境変数設定中..."
export GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
export DB_HOST=${DB_HOST}
export DB_PORT=${DB_PORT}
export DB_NAME=${DB_NAME}
export DB_USER=${DB_USER}
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="

# 3. 仮想環境アクティブ化
echo "3. 仮想環境アクティブ化中..."
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
else
    echo "仮想環境が見つかりません"
    exit 1
fi

# 4. 必要なライブラリ確認・インストール
echo "4. 必要ライブラリの確認中..."
pip install requests > /dev/null 2>&1

# 5. 既存プロセス停止
echo "5. 既存プロセス停止中..."
pkill -f "python.*main.py" > /dev/null 2>&1 || true
sleep 2

# 6. Cloud SQL Proxy確認
echo "6. Cloud SQL Proxy接続確認中..."
if ! curl -s --connect-timeout 2 127.0.0.1:3306 > /dev/null 2>&1; then
    echo "Cloud SQL Proxyが起動していません。起動中..."
    cloud_sql_proxy -instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306 > /dev/null 2>&1 &
    PROXY_PID=$!
    sleep 5
    echo "Cloud SQL Proxy起動完了 (PID: $PROXY_PID)"
fi

# 7. データベース接続テスト
echo "7. データベース接続テスト中..."
python3 -c "
import sys
sys.path.append('.')
from get_info.db_connection import test_connection
if test_connection():
    print('✓ データベース接続成功')
else:
    print('✗ データベース接続失敗')
    sys.exit(1)
"

# 8. Flask サービス起動
echo "8. Flask サービス起動中..."
python main.py > service.log 2>&1 &
FLASK_PID=$!
echo "Flask サービス起動完了 (PID: $FLASK_PID)"

# 9. サービス起動待機
echo "9. サービス起動待機中..."
sleep 5

# 10. ヘルスチェック
echo "10. ヘルスチェック実行中..."
for i in {1..10}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✓ サービス起動確認"
        break
    else
        echo "サービス起動待機中... ($i/10)"
        sleep 2
    fi
    if [ $i -eq 10 ]; then
        echo "✗ サービス起動失敗"
        echo "サービスログ:"
        cat service.log
        exit 1
    fi
done

# 11. APIテスト実行
echo "11. APIテスト実行中..."
python test_real_data.py

# 12. テスト結果確認
TEST_RESULT=$?

# 13. プロセス停止
echo "12. サービス停止中..."
kill $FLASK_PID > /dev/null 2>&1 || true
if [[ -n "$PROXY_PID" ]]; then
    kill $PROXY_PID > /dev/null 2>&1 || true
fi

# 14. 結果表示
echo ""
echo "=== テスト完了 ==="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ すべてのテストが成功しました！"
    echo "✓ DBに存在する実データでの情報取得が正常に動作しています"
else
    echo "✗ テストが失敗しました"
    echo "詳細はログを確認してください"
fi

# 15. ログファイル削除
rm -f service.log

exit $TEST_RESULT 