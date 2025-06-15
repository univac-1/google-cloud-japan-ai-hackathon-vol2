#!/bin/bash
# Cloud Run Jobs デプロイスクリプト
# Cloud Run Jobs のアプリケーションのみをデプロイします

set -e

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 共通関数の読み込み
source "$SCRIPT_DIR/job-functions.sh"

# デフォルト設定
ENVIRONMENT="${ENVIRONMENT:-development}"
LOG_LEVEL="${LOG_LEVEL:-debug}"
JOB_NAME="${JOB_NAME:-anpi-call-create-task-job}"
REGION="${REGION:-asia-northeast1}"
CPU="${CPU:-1}"
MEMORY="${MEMORY:-512Mi}"
TASK_TIMEOUT="${TASK_TIMEOUT:-300}"
MAX_RETRIES="${MAX_RETRIES:-1}"
CLOUD_TASKS_LOCATION="${CLOUD_TASKS_LOCATION:-asia-northeast1}"
CLOUD_TASKS_QUEUE="${CLOUD_TASKS_QUEUE:-anpi-call-queue}"

# プロジェクト設定
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    log_error "プロジェクトIDが設定されていません"
    exit 1
fi

echo ""
echo "=== Cloud Run Jobs デプロイメント開始 ==="
echo ""

log_info "設定情報:"
echo "   プロジェクトID: $PROJECT_ID"
echo "   リージョン: $REGION"
echo "   ジョブ名: $JOB_NAME"
echo "   環境: $ENVIRONMENT"
echo "   CPUリソース: $CPU"
echo "   メモリリソース: $MEMORY"
echo ""

# 使用方法の表示
show_usage() {
    echo "使用方法: $0 [コマンド]"
    echo ""
    echo "利用可能なコマンド:"
    echo "  deploy     - Cloud Run Jobをデプロイ（デフォルト）"
    echo "  build      - Cloud Buildでイメージビルド・デプロイ"
    echo "  execute    - 既存のジョブを手動実行"
    echo "  logs       - ジョブのログを表示"
    echo "  status     - ジョブの実行履歴を表示"
    echo "  delete     - ジョブを削除"
    echo "  help       - このヘルプを表示"
    echo ""
    echo "環境変数での設定例:"
    echo "  ENVIRONMENT=production LOG_LEVEL=info $0 deploy"
    echo ""
}

# Cloud Buildを使用したデプロイ
deploy_with_cloud_build() {
    log_info "Cloud Buildを使用してデプロイ中..."
    
    # Cloud Run Jobs ディレクトリ内でビルド実行
    cd "$SCRIPT_DIR"
    
    # Cloud Build設定の確認
    if [ ! -f "cloudbuild.yaml" ]; then
        log_info "cloudbuild.yamlが見つからないため、デフォルトのコンテナビルドを実行します"
        deploy_with_container_build
        return $?
    fi
    
    # Cloud Buildの実行
    gcloud builds submit --config cloudbuild.yaml \
        --substitutions="_JOB_NAME=$JOB_NAME,_REGION=$REGION,_CPU=$CPU,_MEMORY=$MEMORY,_TASK_TIMEOUT=$TASK_TIMEOUT,_ENVIRONMENT=$ENVIRONMENT,_LOG_LEVEL=$LOG_LEVEL"
    
    if [ $? -eq 0 ]; then
        log_success "Cloud Buildデプロイが完了しました"
        return 0
    else
        log_error "Cloud Buildデプロイに失敗しました"
        return 1
    fi
}

# コンテナビルドとデプロイ
deploy_with_container_build() {
    log_info "コンテナをビルドしてデプロイ中..."
    
    cd "$SCRIPT_DIR"
    
    # イメージ名の構築
    IMAGE_NAME="gcr.io/$PROJECT_ID/anpi-call-scheduler:latest"
    
    # Dockerイメージのビルド
    log_info "コンテナイメージをビルド中: $IMAGE_NAME"
    gcloud builds submit --tag "$IMAGE_NAME" .
    
    if [ $? -ne 0 ]; then
        log_error "コンテナイメージのビルドに失敗しました"
        return 1
    fi
    
    # Cloud Run Jobの作成・更新
    deploy_job_with_image "$IMAGE_NAME"
    return $?
}

# YAMLファイルを使用したデプロイ
deploy_with_yaml() {
    log_info "YAMLファイルを使用してデプロイ中..."
    
    cd "$SCRIPT_DIR"
    
    # job.yamlの確認
    if [ ! -f "job.yaml" ]; then
        log_error "job.yamlが見つかりません"
        return 1
    fi
    
    # まずコンテナイメージをビルド
    IMAGE_NAME="gcr.io/$PROJECT_ID/anpi-call-scheduler:latest"
    log_info "コンテナイメージをビルド中: $IMAGE_NAME"
    
    gcloud builds submit --tag "$IMAGE_NAME" .
    if [ $? -ne 0 ]; then
        log_error "コンテナイメージのビルドに失敗しました"
        return 1
    fi
    
    # 環境変数の設定とYAMLの置換
    export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
    export JOB_NAME="$JOB_NAME"
    export IMAGE_URL="$IMAGE_NAME"
    export TASK_TIMEOUT="$TASK_TIMEOUT"
    export CPU="$CPU"
    export MEMORY="$MEMORY"
    export ENVIRONMENT="$ENVIRONMENT"
    export LOG_LEVEL="$LOG_LEVEL"
    export CLOUD_TASKS_LOCATION="$CLOUD_TASKS_LOCATION"
    export CLOUD_TASKS_QUEUE="$CLOUD_TASKS_QUEUE"
    export MAX_RETRIES="$MAX_RETRIES"
    
    # テンプレートファイルから実際のYAMLを生成
    local temp_yaml="job-temp.yaml"
    if substitute_env_vars_in_yaml "job.yaml" "$temp_yaml"; then
        # デプロイの実行
        log_info "Cloud Run Jobをデプロイ中..."
        gcloud run jobs replace "$temp_yaml" --region="$REGION" --quiet
        
        if [ $? -eq 0 ]; then
            log_success "Cloud Run Jobのデプロイが完了しました"
            rm -f "$temp_yaml"
            return 0
        else
            log_error "Cloud Run Jobのデプロイに失敗しました"
            rm -f "$temp_yaml"
            return 1
        fi
    else
        log_error "YAMLファイルの環境変数置換に失敗しました"
        return 1
    fi
}
        if deploy_cloud_run_job_with_yaml "$temp_yaml" "$REGION"; then
            rm -f "$temp_yaml"
            log_success "YAMLデプロイが完了しました"
            return 0
        else
            rm -f "$temp_yaml"
            log_error "YAMLデプロイに失敗しました"
            return 1
        fi
    else
        return 1
    fi
}

# ジョブの手動実行
execute_job() {
    log_info "Cloud Run Jobを手動実行します"
    
    if execute_cloud_run_job "$JOB_NAME" "$REGION"; then
        echo ""
        log_info "実行状況は以下のコマンドで確認できます:"
        echo "  $0 status"
        echo "  $0 logs"
        return 0
    else
        return 1
    fi
}

# ジョブのログ表示
show_logs() {
    log_info "Cloud Run Jobのログを表示します"
    get_job_logs "$JOB_NAME" 50
}

# ジョブの状態表示
show_status() {
    log_info "Cloud Run Jobの実行履歴を表示します"
    get_job_executions "$JOB_NAME" "$REGION" 10
}

# ジョブの削除
delete_job() {
    log_warning "Cloud Run Jobを削除しようとしています: $JOB_NAME"
    echo "この操作は元に戻せません。続行しますか？ (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if delete_cloud_run_job "$JOB_NAME" "$REGION"; then
            log_success "Cloud Run Jobが削除されました"
        else
            log_error "Cloud Run Jobの削除に失敗しました"
            return 1
        fi
    else
        log_info "削除をキャンセルしました"
    fi
}

# メインデプロイ処理
main_deploy() {
    log_info "Cloud Run Jobのデプロイを開始します"
    
    # 前提条件の確認
    log_info "前提条件を確認中..."
    
    # Cloud Tasksキューの存在確認
    if [ -f "../cloud-tasks/tasks-functions.sh" ]; then
        source "../cloud-tasks/tasks-functions.sh"
        if ! check_tasks_queue_status "$CLOUD_TASKS_QUEUE" "$CLOUD_TASKS_LOCATION" >/dev/null 2>&1; then
            log_warning "Cloud Tasksキューが見つかりません: $CLOUD_TASKS_QUEUE"
            log_info "先に以下のコマンドを実行してください:"
            echo "  ../setup-infrastructure.sh"
            echo "  または"
            echo "  ../cloud-tasks/deploy-cloud-tasks.sh deploy"
            log_info "継続してデプロイを実行します..."
        else
            log_success "Cloud Tasksキューが確認できました"
        fi
    else
        log_warning "Cloud Tasksキューの確認をスキップしました"
    fi
    
    # デプロイ方法の選択（Cloud Build優先）
    if [ -f "cloudbuild.yaml" ]; then
        deploy_with_cloud_build
    elif [ -f "job.yaml" ]; then
        deploy_with_yaml
    else
        log_error "デプロイ設定ファイル（cloudbuild.yaml または job.yaml）が見つかりません"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        echo ""
        log_success "=== Cloud Run Jobs デプロイメント完了 ==="
        echo ""
        log_info "次に利用可能なコマンド:"
        echo "  # ジョブの手動実行"
        echo "  $0 execute"
        echo ""
        echo "  # 実行履歴の確認"
        echo "  $0 status"  
        echo ""
        echo "  # ログの確認"
        echo "  $0 logs"
        echo ""
        echo "  # Cloud Schedulerの設定（必要に応じて）"
        echo "  ../cloud-scheduler/deploy-scheduler.sh"
        echo ""
        return 0
    else
        log_error "デプロイに失敗しました"
        return 1
    fi
}

# コマンドライン引数の処理
case "${1:-deploy}" in
    "deploy")
        main_deploy
        ;;
    "build")
        deploy_with_cloud_build
        ;;
    "execute")
        execute_job
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "delete")
        delete_job
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        log_error "不明なコマンド: $1"
        show_usage
        exit 1
        ;;
esac
