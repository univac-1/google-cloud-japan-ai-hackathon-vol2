#!/bin/bash
# Cloud Tasks キュー作成・管理の共通関数
# anpi-call-scheduler/cloud-tasks/tasks-functions.sh

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cloud Tasksキュー作成関数
create_cloud_tasks_queue() {
    local PROJECT_ID=$1
    local LOCATION=$2
    local QUEUE_NAME=$3
    local MAX_CONCURRENT_DISPATCHES=${4:-100}
    local MAX_RETRY_DURATION=${5:-3600s}
    local MAX_ATTEMPTS=${6:-3}
    local MIN_BACKOFF=${7:-10s}
    local MAX_BACKOFF=${8:-300s}

    echo -e "${YELLOW}📋 Cloud Tasksキューを設定中...${NC}"

    # パラメータ検証
    if [ -z "$PROJECT_ID" ] || [ -z "$LOCATION" ] || [ -z "$QUEUE_NAME" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: create_cloud_tasks_queue PROJECT_ID LOCATION QUEUE_NAME [MAX_CONCURRENT_DISPATCHES] [MAX_RETRY_DURATION] [MAX_ATTEMPTS] [MIN_BACKOFF] [MAX_BACKOFF]"
        return 1
    fi

    # Cloud Tasks APIの有効化確認
    echo -e "${YELLOW}   Cloud Tasks APIの確認中...${NC}"
    if ! gcloud services list --enabled --filter="name:cloudtasks.googleapis.com" --format="value(name)" | grep -q "cloudtasks.googleapis.com"; then
        echo -e "${YELLOW}   Cloud Tasks APIを有効化中...${NC}"
        gcloud services enable cloudtasks.googleapis.com
        echo -e "${GREEN}   ✓ Cloud Tasks APIを有効化しました${NC}"
    else
        echo -e "${GREEN}   ✓ Cloud Tasks APIは有効化済み${NC}"
    fi

    # 既存キューの確認
    echo -e "${YELLOW}   既存のCloud Tasksキューの確認中...${NC}"
    if gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ キュー '$QUEUE_NAME' は既に存在します${NC}"
        
        # キュー設定の詳細を表示（参考情報）
        echo -e "${BLUE}   キュー詳細情報:${NC}"
        gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION --format="table(
            name.basename():label=QUEUE_NAME,
            rateLimits.maxConcurrentDispatches:label=MAX_CONCURRENT,
            retryConfig.maxRetryDuration:label=MAX_RETRY_DURATION,
            retryConfig.maxAttempts:label=MAX_ATTEMPTS
        )"
        return 0
    fi

    # キューの作成
    echo -e "${YELLOW}   Cloud Tasksキューを作成中...${NC}"
    if gcloud tasks queues create $QUEUE_NAME \
        --location=$LOCATION \
        --max-concurrent-dispatches=$MAX_CONCURRENT_DISPATCHES \
        --max-retry-duration=$MAX_RETRY_DURATION \
        --max-attempts=$MAX_ATTEMPTS \
        --min-backoff=$MIN_BACKOFF \
        --max-backoff=$MAX_BACKOFF >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Tasksキューが作成されました${NC}"
    else
        echo -e "${RED}   ❌ Cloud Tasksキューの作成に失敗しました${NC}"
        return 1
    fi

    return 0
}

# Cloud Tasksキューの状態確認関数
check_tasks_queue_status() {
    local QUEUE_NAME=$1
    local LOCATION=$2

    if [ -z "$QUEUE_NAME" ] || [ -z "$LOCATION" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: check_tasks_queue_status QUEUE_NAME LOCATION"
        return 1
    fi

    echo -e "${YELLOW}📋 Cloud Tasksキューの状態確認中...${NC}"

    if gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ キュー '$QUEUE_NAME' が存在します${NC}"
        
        # キューの詳細状態を表示
        gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION --format="table(
            name.basename():label=QUEUE_NAME,
            state:label=STATE,
            rateLimits.maxConcurrentDispatches:label=MAX_CONCURRENT,
            retryConfig.maxRetryDuration:label=MAX_RETRY_DURATION,
            retryConfig.maxAttempts:label=MAX_ATTEMPTS,
            retryConfig.minBackoff:label=MIN_BACKOFF,
            retryConfig.maxBackoff:label=MAX_BACKOFF
        )"
        
        # キュー内のタスク数を表示
        local TASK_COUNT
        TASK_COUNT=$(gcloud tasks list --queue=$QUEUE_NAME --location=$LOCATION --format="value(name)" 2>/dev/null | wc -l)
        echo -e "${BLUE}   キュー内のタスク数: $TASK_COUNT${NC}"
        
        return 0
    else
        echo -e "${RED}   ❌ キュー '$QUEUE_NAME' が見つかりません${NC}"
        return 1
    fi
}

# Cloud Tasksキューのタスク一覧表示関数
list_tasks_in_queue() {
    local QUEUE_NAME=$1
    local LOCATION=$2
    local LIMIT=${3:-10}

    if [ -z "$QUEUE_NAME" ] || [ -z "$LOCATION" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: list_tasks_in_queue QUEUE_NAME LOCATION [LIMIT]"
        return 1
    fi

    echo -e "${YELLOW}📋 キュー内のタスク一覧 (最新${LIMIT}件):${NC}"

    if gcloud tasks list --queue=$QUEUE_NAME --location=$LOCATION --limit=$LIMIT --format="table(
        name.basename():label=TASK_NAME,
        scheduleTime:label=SCHEDULE_TIME,
        httpRequest.url:label=TARGET_URL,
        createTime:label=CREATED_TIME
    )" 2>/dev/null; then
        return 0
    else
        echo -e "${RED}   ❌ タスク一覧の取得に失敗しました${NC}"
        return 1
    fi
}

# Cloud Tasksキュー削除関数（管理用）
delete_cloud_tasks_queue() {
    local QUEUE_NAME=$1
    local LOCATION=$2
    local FORCE=${3:-false}

    if [ -z "$QUEUE_NAME" ] || [ -z "$LOCATION" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: delete_cloud_tasks_queue QUEUE_NAME LOCATION [FORCE]"
        return 1
    fi

    echo -e "${YELLOW}⚠️  Cloud Tasksキューを削除中...${NC}"

    if [ "$FORCE" != "true" ]; then
        echo -e "${RED}警告: この操作によりキュー '$QUEUE_NAME' とその中のすべてのタスクが削除されます${NC}"
        read -p "続行しますか? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}操作がキャンセルされました${NC}"
            return 1
        fi
    fi

    if gcloud tasks queues delete $QUEUE_NAME --location=$LOCATION --quiet >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Tasksキューが削除されました${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Cloud Tasksキューの削除に失敗しました${NC}"
        return 1
    fi
}

# Cloud Tasksキューの一時停止/再開関数
pause_cloud_tasks_queue() {
    local QUEUE_NAME=$1
    local LOCATION=$2

    if [ -z "$QUEUE_NAME" ] || [ -z "$LOCATION" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: pause_cloud_tasks_queue QUEUE_NAME LOCATION"
        return 1
    fi

    echo -e "${YELLOW}⏸️  Cloud Tasksキューを一時停止中...${NC}"

    if gcloud tasks queues pause $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Tasksキューが一時停止されました${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Cloud Tasksキューの一時停止に失敗しました${NC}"
        return 1
    fi
}

resume_cloud_tasks_queue() {
    local QUEUE_NAME=$1
    local LOCATION=$2

    if [ -z "$QUEUE_NAME" ] || [ -z "$LOCATION" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: resume_cloud_tasks_queue QUEUE_NAME LOCATION"
        return 1
    fi

    echo -e "${YELLOW}▶️  Cloud Tasksキューを再開中...${NC}"

    if gcloud tasks queues resume $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Tasksキューが再開されました${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Cloud Tasksキューの再開に失敗しました${NC}"
        return 1
    fi
}

# メイン処理（直接実行時のテスト用）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${BLUE}Cloud Tasks 共通関数ライブラリ${NC}"
    echo -e "${YELLOW}利用可能な関数:${NC}"
    echo "  - create_cloud_tasks_queue: Cloud Tasksキューの作成"
    echo "  - check_tasks_queue_status: キューの状態確認"
    echo "  - list_tasks_in_queue: キュー内のタスク一覧表示"
    echo "  - delete_cloud_tasks_queue: キューの削除"
    echo "  - pause_cloud_tasks_queue: キューの一時停止"
    echo "  - resume_cloud_tasks_queue: キューの再開"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  source ./cloud-tasks/tasks-functions.sh"
    echo "  create_cloud_tasks_queue \$PROJECT_ID \$LOCATION \$QUEUE_NAME"
fi
