#!/bin/bash
# Cloud Run Jobs 共通関数ライブラリ
# このファイルは他のスクリプトからsourceして利用する

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

log_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

# Cloud Run Jobの存在確認
check_cloud_run_job_exists() {
    local job_name="$1"
    local region="$2"
    
    if [ -z "$job_name" ] || [ -z "$region" ]; then
        log_error "ジョブ名とリージョンが必要です"
        return 1
    fi
    
    if gcloud run jobs describe "$job_name" --region="$region" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Cloud Run Jobのデプロイ（YAML使用）
deploy_cloud_run_job_with_yaml() {
    local yaml_file="$1"
    local region="$2"
    
    if [ -z "$yaml_file" ] || [ -z "$region" ]; then
        log_error "YAMLファイルとリージョンが必要です"
        return 1
    fi
    
    if [ ! -f "$yaml_file" ]; then
        log_error "YAMLファイルが見つかりません: $yaml_file"
        return 1
    fi
    
    log_info "Cloud Run JobをYAMLファイルでデプロイ中: $yaml_file"
    
    if gcloud run jobs replace "$yaml_file" --region="$region"; then
        log_success "Cloud Run Jobのデプロイが完了しました"
        return 0
    else
        log_error "Cloud Run Jobのデプロイに失敗しました"
        return 1
    fi
}

# Cloud Run Jobのデプロイ（コマンドライン使用）
deploy_cloud_run_job_with_command() {
    local job_name="$1"
    local image="$2"
    local region="$3"
    local cpu="${4:-1}"
    local memory="${5:-512Mi}"
    local timeout="${6:-300}"
    local max_retries="${7:-1}"
    local env_vars="$8"
    local cloudsql_instances="$9"
    
    if [ -z "$job_name" ] || [ -z "$image" ] || [ -z "$region" ]; then
        log_error "ジョブ名、イメージ、リージョンが必要です"
        return 1
    fi
    
    log_info "Cloud Run Jobをコマンドラインでデプロイ中: $job_name"
    
    local deploy_cmd="gcloud run jobs deploy $job_name \
        --image=$image \
        --region=$region \
        --cpu=$cpu \
        --memory=$memory \
        --task-timeout=${timeout}s \
        --max-retries=$max_retries"
    
    # 環境変数の追加
    if [ -n "$env_vars" ]; then
        deploy_cmd="$deploy_cmd --set-env-vars=$env_vars"
    fi
    
    # Cloud SQL接続の追加
    if [ -n "$cloudsql_instances" ]; then
        deploy_cmd="$deploy_cmd --set-cloudsql-instances=$cloudsql_instances"
    fi
    
    if eval "$deploy_cmd"; then
        log_success "Cloud Run Jobのデプロイが完了しました"
        return 0
    else
        log_error "Cloud Run Jobのデプロイに失敗しました"
        return 1
    fi
}

# Cloud Run Jobの手動実行
execute_cloud_run_job() {
    local job_name="$1"
    local region="$2"
    
    if [ -z "$job_name" ] || [ -z "$region" ]; then
        log_error "ジョブ名とリージョンが必要です"
        return 1
    fi
    
    log_info "Cloud Run Jobを手動実行中: $job_name"
    
    if gcloud run jobs execute "$job_name" --region="$region"; then
        log_success "Cloud Run Jobの実行が開始されました"
        return 0
    else
        log_error "Cloud Run Jobの実行に失敗しました"
        return 1
    fi
}

# Cloud Run Jobの実行履歴確認
get_job_executions() {
    local job_name="$1"
    local region="$2"
    local limit="${3:-5}"
    
    if [ -z "$job_name" ] || [ -z "$region" ]; then
        log_error "ジョブ名とリージョンが必要です"
        return 1
    fi
    
    log_info "Cloud Run Jobの実行履歴を確認中: $job_name"
    
    gcloud run jobs executions list \
        --job="$job_name" \
        --region="$region" \
        --limit="$limit" \
        --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status,metadata.creationTimestamp)"
}

# Cloud Run Jobのログ確認
get_job_logs() {
    local job_name="$1"
    local limit="${2:-20}"
    
    if [ -z "$job_name" ]; then
        log_error "ジョブ名が必要です"
        return 1
    fi
    
    log_info "Cloud Run Jobのログを確認中: $job_name"
    
    gcloud logging read \
        "resource.type=cloud_run_job AND resource.labels.job_name=$job_name" \
        --limit="$limit" \
        --format="table(timestamp,severity,textPayload)"
}

# Cloud Run Jobの削除
delete_cloud_run_job() {
    local job_name="$1"
    local region="$2"
    local force="${3:-false}"
    
    if [ -z "$job_name" ] || [ -z "$region" ]; then
        log_error "ジョブ名とリージョンが必要です"
        return 1
    fi
    
    if [ "$force" = "true" ]; then
        log_warning "Cloud Run Jobを強制削除中: $job_name"
        gcloud run jobs delete "$job_name" --region="$region" --quiet
    else
        log_info "Cloud Run Jobを削除中: $job_name"
        gcloud run jobs delete "$job_name" --region="$region"
    fi
}

# YAMLファイルの環境変数置換
substitute_env_vars_in_yaml() {
    local input_file="$1"
    local output_file="$2"
    
    if [ -z "$input_file" ] || [ -z "$output_file" ]; then
        log_error "入力ファイルと出力ファイルが必要です"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        log_error "入力ファイルが見つかりません: $input_file"
        return 1
    fi
    
    # 環境変数を置換してファイルに出力
    envsubst < "$input_file" > "$output_file"
    
    if [ $? -eq 0 ]; then
        log_info "環境変数置換が完了しました: $output_file"
        return 0
    else
        log_error "環境変数置換に失敗しました"
        return 1
    fi
}

# コンテナイメージを使ったCloud Run Jobのデプロイ
deploy_job_with_image() {
    local image_name="$1"
    
    if [ -z "$image_name" ]; then
        log_error "イメージ名が必要です"
        return 1
    fi
    
    log_info "Cloud Run Jobをデプロイ中: $JOB_NAME"
    
    # Cloud Run Jobが既に存在するかチェック
    if check_cloud_run_job_exists "$JOB_NAME" "$REGION"; then
        log_info "既存のCloud Run Jobを更新中..."
        gcloud run jobs update "$JOB_NAME" \
            --image="$image_name" \
            --region="$REGION" \
            --cpu="$CPU" \
            --memory="$MEMORY" \
            --task-timeout="$TASK_TIMEOUT" \
            --max-retries="$MAX_RETRIES" \
            --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=$LOG_LEVEL,CLOUD_TASKS_LOCATION=$CLOUD_TASKS_LOCATION,CLOUD_TASKS_QUEUE=$CLOUD_TASKS_QUEUE,USE_CLOUD_SQL=true,IS_CLOUD_RUN_JOB=true" \
            --set-cloudsql-instances="$PROJECT_ID:asia-northeast1:cloudsql-01" \
            --quiet
    else
        log_info "新しいCloud Run Jobを作成中..."
        gcloud run jobs create "$JOB_NAME" \
            --image="$image_name" \
            --region="$REGION" \
            --cpu="$CPU" \
            --memory="$MEMORY" \
            --task-timeout="$TASK_TIMEOUT" \
            --max-retries="$MAX_RETRIES" \
            --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=$LOG_LEVEL,CLOUD_TASKS_LOCATION=$CLOUD_TASKS_LOCATION,CLOUD_TASKS_QUEUE=$CLOUD_TASKS_QUEUE,USE_CLOUD_SQL=true,IS_CLOUD_RUN_JOB=true" \
            --set-cloudsql-instances="$PROJECT_ID:asia-northeast1:cloudsql-01" \
            --quiet
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Cloud Run Jobのデプロイが完了しました: $JOB_NAME"
        return 0
    else
        log_error "Cloud Run Jobのデプロイに失敗しました"
        return 1
    fi
}

# Cloud Run Job設定の検証
validate_job_config() {
    local yaml_file="$1"
    
    if [ -z "$yaml_file" ]; then
        log_error "YAMLファイルが必要です"
        return 1
    fi
    
    if [ ! -f "$yaml_file" ]; then
        log_error "YAMLファイルが見つかりません: $yaml_file"
        return 1
    fi
    
    log_info "Cloud Run Job設定を検証中: $yaml_file"
    
    # 基本的な YAML 構文チェック
    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        log_success "YAML構文は正常です"
    else
        log_error "YAML構文エラーが検出されました"
        return 1
    fi
    
    # 必須フィールドの確認
    local required_fields=("metadata.name" "spec.template.spec.template.spec.containers[0].image")
    for field in "${required_fields[@]}"; do
        if yq eval ".$field" "$yaml_file" >/dev/null 2>&1; then
            log_success "必須フィールドが存在します: $field"
        else
            log_warning "必須フィールドが見つかりません: $field"
        fi
    done
    
    return 0
}
