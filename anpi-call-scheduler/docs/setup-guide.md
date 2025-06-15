# セットアップガイド

## 前提条件

### 必要なツール

- Google Cloud SDK (gcloud CLI)
- Docker (ローカル開発時のみ)
- Python 3.12+ (ローカル開発時のみ)

### 必要な権限

以下のIAMロールが必要です：

- **Cloud Run Admin** - Cloud Run Jobsの管理
- **Cloud Build Editor** - CI/CDパイプラインの実行
- **Service Account User** - サービスアカウントの使用
- **Cloud Scheduler Admin** - スケジューラーの設定
- **Project Editor** - プロジェクト全体の設定変更
- **Container Registry Admin** - コンテナイメージの管理

## 初期設定

### 1. GCP認証設定

```bash
# GCPにログイン
gcloud auth login

# アプリケーションのデフォルト認証を設定
gcloud auth application-default login

# 利用可能なプロジェクトを確認
gcloud projects list

# 使用するプロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 現在の設定を確認
gcloud config list
```

### 2. 必要なAPIの有効化

```bash
# 必要なAPIを一括で有効化
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudscheduler.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

### 3. 環境設定ファイルの確認

`.env`ファイルを確認し、必要に応じて編集してください：

```bash
# 設定ファイルの内容を確認
cat .env

# 設定ファイルを編集（必要に応じて）
nano .env
```

### 4. 初回デプロイ

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy-complete.sh

# 初回デプロイを実行
./deploy-complete.sh
```

## 設定パラメータ

| パラメータ | 説明 | デフォルト値 |
|-----------|------|-------------|
| ENVIRONMENT | 実行環境 | development |
| LOG_LEVEL | ログレベル | debug |
| JOB_NAME | Cloud Run Job名 | anpi-call-scheduler-dev |
| REGION | デプロイリージョン | asia-northeast1 |
| SCHEDULE | 実行スケジュール（cron形式） | "*/15 * * * *" |
| SCHEDULER_NAME | Cloud Scheduler名 | anpi-call-scheduler-dev-hourly |
| CPU | CPUリソース | 1 |
| MEMORY | メモリリソース | 512Mi |
| TASK_TIMEOUT | タスクタイムアウト（秒） | 300 |
| MAX_RETRIES | 最大リトライ回数 | 1 |

## 環境別設定

### 開発環境 (development)

- ログレベル: debug
- 詳細な実行ログを出力
- 手動実行とスケジュール実行の両方をサポート

### 本番環境 (production)

本番環境用の設定例：

```bash
ENVIRONMENT=production
LOG_LEVEL=info
JOB_NAME=anpi-call-scheduler-prod
SCHEDULER_NAME=anpi-call-scheduler-prod-hourly
CPU=2
MEMORY=1Gi
TASK_TIMEOUT=600
MAX_RETRIES=3
```

## 動作確認

### 手動実行

```bash
# Cloud Run Jobの手動実行
gcloud run jobs execute anpi-call-scheduler-dev --region=asia-northeast1

# Cloud Schedulerの手動実行
gcloud scheduler jobs run anpi-call-scheduler-dev-hourly --location=asia-northeast1
```

### ログ確認

```bash
# 最新のジョブ実行ログを確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-scheduler-dev" \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)"

# 実行履歴の確認
gcloud run jobs executions list \
    --job=anpi-call-scheduler-dev \
    --region=asia-northeast1 \
    --limit=10
```

### ステータス確認

```bash
# Cloud Run Jobの詳細確認
gcloud run jobs describe anpi-call-scheduler-dev --region=asia-northeast1

# Cloud Schedulerの状態確認
gcloud scheduler jobs describe anpi-call-scheduler-dev-hourly --location=asia-northeast1
```

## セキュリティ設定

### サービスアカウント

デフォルトでは以下のサービスアカウントを使用します：

- **Cloud Build**: `{PROJECT_NUMBER}@cloudbuild.gserviceaccount.com`
- **Cloud Scheduler**: `{PROJECT_NUMBER}-compute@developer.gserviceaccount.com`
- **Cloud Run**: デフォルトのCompute Engineサービスアカウント

### 最小権限の原則

本番環境では、カスタムサービスアカウントを作成し、必要最小限の権限のみを付与することを推奨します。
