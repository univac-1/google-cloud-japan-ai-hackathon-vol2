#!/bin/bash
# Cloud Tasks専用デプロイスクリプト
# anpi-call-scheduler/cloud-tasks/deploy-cloud-tasks.sh

set -e

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 共通関数の読み込み
source "$SCRIPT_DIR/tasks-functions.sh"

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 引数処理
ACTION=${1:-"deploy"}
PROJECT_ID=${2:-$(gcloud config get-value project)}

# 設定変数（環境変数による上書き可能）
LOCATION=${CLOUD_TASKS_LOCATION:-"asia-northeast1"}
QUEUE_NAME=${CLOUD_TASKS_QUEUE:-"anpi-call-queue"}
MAX_CONCURRENT_DISPATCHES=${MAX_CONCURRENT_DISPATCHES:-100}
MAX_RETRY_DURATION=${MAX_RETRY_DURATION:-"3600s"}
MAX_ATTEMPTS=${MAX_ATTEMPTS:-3}
MIN_BACKOFF=${MIN_BACKOFF:-"10s"}
MAX_BACKOFF=${MAX_BACKOFF:-"300s"}

# 環境設定
ENVIRONMENT=${ENVIRONMENT:-"development"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 使用方法表示関数
show_usage() {
    echo "使用方法: $0 [ACTION] [PROJECT_ID]"
    echo ""
    echo "ACTION:"
    echo "  deploy    - Cloud Tasksキューをデプロイ（デフォルト）"
    echo "  status    - Cloud Tasksキューの状態確認"
    echo "  list      - キュー内のタスク一覧表示"
    echo "  pause     - キューの一時停止"
    echo "  resume    - キューの再開"
    echo "  delete    - キューの削除（注意）"
    echo "  help      - このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 deploy my-project-id"
    echo "  $0 status"
    echo "  $0 list"
}

# メイン処理
case "$ACTION" in
    "deploy")
        echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║               Cloud Tasks デプロイメント                    ║${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        echo -e "${YELLOW}📋 設定情報:${NC}"
        echo -e "   プロジェクトID: ${GREEN}$PROJECT_ID${NC}"
        echo -e "   ロケーション: ${GREEN}$LOCATION${NC}"
        echo -e "   キュー名: ${GREEN}$QUEUE_NAME${NC}"
        echo ""
        
        if create_cloud_tasks_queue "$PROJECT_ID" "$LOCATION" "$QUEUE_NAME" "$MAX_CONCURRENT_DISPATCHES" "$MAX_RETRY_DURATION" "$MAX_ATTEMPTS" "$MIN_BACKOFF" "$MAX_BACKOFF"; then
            echo -e "${GREEN}🎉 Cloud Tasksデプロイメント完了！${NC}"
        else
            echo -e "${RED}❌ Cloud Tasksデプロイメントに失敗しました${NC}"
            exit 1
        fi
        ;;
        
    "status")
        echo -e "${BLUE}📋 Cloud Tasksキューの状態確認${NC}"
        check_tasks_queue_status "$QUEUE_NAME" "$LOCATION"
        ;;
        
    "list")
        echo -e "${BLUE}📋 Cloud Tasksキューのタスク一覧${NC}"
        list_tasks_in_queue "$QUEUE_NAME" "$LOCATION" 20
        ;;
        
    "pause")
        echo -e "${BLUE}⏸️  Cloud Tasksキューの一時停止${NC}"
        pause_cloud_tasks_queue "$QUEUE_NAME" "$LOCATION"
        ;;
        
    "resume")
        echo -e "${BLUE}▶️  Cloud Tasksキューの再開${NC}"
        resume_cloud_tasks_queue "$QUEUE_NAME" "$LOCATION"
        ;;
        
    "delete")
        echo -e "${BLUE}🗑️  Cloud Tasksキューの削除${NC}"
        delete_cloud_tasks_queue "$QUEUE_NAME" "$LOCATION"
        ;;
        
    "help"|"-h"|"--help")
        show_usage
        ;;
        
    *)
        echo -e "${RED}❌ 不明なアクション: $ACTION${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
