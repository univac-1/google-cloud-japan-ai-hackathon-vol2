# Cloud Run Jobs - 安否確認コールシステム

本ディレクトリは、安否確認コールシステムで使用するCloud Run Jobsの作成・管理を行う専用資材です。

## 機能概要

### 📞 即時実行機能
- **現在時刻チェック**: データベースのユーザーテーブルを確認し、現在時刻に基づいて即座に電話をかけるべき対象者を特定
- **許容時間設定**: 指定時刻の前後5分（設定可能）以内なら即時実行対象として判定
- **即時タスク作成**: 対象者に対して即座にCloud Tasksタスクを作成・実行

### 🔄 処理フロー
1. **データベース接続**: Cloud SQLに接続してユーザー情報を取得
2. **即時実行判定**: 現在時刻と各ユーザーの設定時刻（曜日・時刻）を比較
3. **タスク作成**: 即時実行対象者のCloud Tasksタスクを作成
4. **ログ出力**: 処理結果と作成タスク数をログに記録

### 💡 アプリケーションの仕様
このアプリケーションは**即時実行専用**に設計されています：
- 将来のスケジューリング機能は実装されていません
- 現在時刻に基づいて、今すぐ電話をかけるべきユーザーのみを処理します
- 定期的に実行（例：毎分）することで、適切なタイミングでの安否確認呼び出しを実現します

## ディレクトリ構成

```
cloud-run-jobs/
├── main.py                   # メインアプリケーション（即時実行安否確認スケジューラー）
├── requirements.txt          # Python依存関係
├── Dockerfile               # Cloud Run Jobs用Dockerイメージ定義
├── cloudbuild.yaml          # Cloud Build設定
├── job.yaml                 # Cloud Run Job定義
├── job-functions.sh         # Cloud Run Jobs 共通関数ライブラリ  
├── deploy-job.sh           # Cloud Run Jobs管理スクリプト（統合コマンド）
├── job-config.env          # Cloud Run Jobs設定定義
└── README.md               # このファイル
```

## 主要ファイル

| ファイル名 | 用途 | 説明 |
|-----------|------|------|
| `main.py` | アプリケーション | 即時実行専用の安否確認スケジューラー |
| `requirements.txt` | 依存関係 | Python パッケージの依存関係定義 |
| `Dockerfile` | コンテナ定義 | Cloud Run Jobs用のDockerイメージ定義 |
| `cloudbuild.yaml` | ビルド設定 | Cloud Buildでのビルド・デプロイ設定 |
| `job.yaml` | ジョブ定義 | Cloud Run Jobの設定定義 |
| `job-functions.sh` | 共通関数 | ジョブデプロイ・実行・管理などの再利用可能な関数 |
| `deploy-job.sh` | 管理スクリプト | デプロイ・実行・ログ確認・管理操作の統合コマンド |
| `job-config.env` | 設定定義 | ジョブの設定値を一元管理 |

## 使用方法

### 🚀 クイックデプロイ（推奨）

Cloud Run Jobを自動デプロイ：

```bash
# Cloud Run Jobs 単体デプロイ
./cloud-run-jobs/deploy-job.sh deploy

# または Cloud Build を使用したデプロイ
./cloud-run-jobs/deploy-job.sh build
```

### 📋 管理コマンド

新しい管理スクリプトを使用して各種操作を実行：

```bash
# ジョブのデプロイ（デフォルト）
./cloud-run-jobs/deploy-job.sh deploy

# Cloud Buildでビルド・デプロイ
./cloud-run-jobs/deploy-job.sh build

# ジョブの手動実行
./cloud-run-jobs/deploy-job.sh execute

# ジョブの実行履歴確認
./cloud-run-jobs/deploy-job.sh status

# ジョブのログ確認
./cloud-run-jobs/deploy-job.sh logs

# ジョブの削除
./cloud-run-jobs/deploy-job.sh delete

# ヘルプ表示
./cloud-run-jobs/deploy-job.sh help
```

### 🔧 設定のカスタマイズ

環境変数で設定をオーバーライド可能：

```bash
# 本番環境でのデプロイ例
ENVIRONMENT=production LOG_LEVEL=info ./cloud-run-jobs/deploy-job.sh build

# リソース設定のカスタマイズ例
CPU=2 MEMORY=1Gi TASK_TIMEOUT=600 ./cloud-run-jobs/deploy-job.sh deploy
```
./cloud-run-jobs/deploy-job.sh logs

# ジョブの削除
./cloud-run-jobs/deploy-job.sh delete

# ヘルプ表示
./cloud-run-jobs/deploy-job.sh help
```

### 🔧 環境変数設定

環境変数で設定をカスタマイズ：

```bash
# 環境変数の設定例
export ENVIRONMENT="production"
export LOG_LEVEL="info"
export JOB_NAME="anpi-call-scheduler-prod"
export CPU="2"
export MEMORY="1Gi"
export TASK_TIMEOUT="600"

# デプロイ実行
./cloud-run-jobs/deploy-job.sh deploy
```

### 🔧 即時実行機能の設定

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `IMMEDIATE_CALL_TOLERANCE_MINUTES` | 即時実行の許容時間（分） | `5` | `10` |

### 基本設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `ENVIRONMENT` | 実行環境 | `development` |
| `LOG_LEVEL` | ログレベル | `debug` |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | `univac-aiagent` |
| `CLOUD_TASKS_LOCATION` | Cloud Tasksのロケーション | `asia-northeast1` |
| `CLOUD_TASKS_QUEUE` | Cloud Tasksキュー名 | `anpi-call-queue` |
| `ANPI_CALL_URL` | 安否確認サービスURL | `https://httpbin.org/post` |

### データベース設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `USE_CLOUD_SQL` | Cloud SQL使用フラグ | `true` |
| `DB_USER` | データベースユーザー | `default` |
| `DB_PASSWORD` | データベースパスワード | - |
| `DB_NAME` | データベース名 | `default` |

### 設定例

```bash
# 即時実行の許容時間を10分に設定
export IMMEDIATE_CALL_TOLERANCE_MINUTES="10"

# 本番環境設定
export ENVIRONMENT="production"
export LOG_LEVEL="info"

# デプロイ実行
./cloud-run-jobs/deploy-job.sh build
```

### 🔗 メインデプロイスクリプトとの統合

`deploy-complete.sh`からは自動的にこのディレクトリの機能が呼び出されます：

```bash
# メインデプロイスクリプトの実行
./deploy-complete.sh

# Cloud Run Jobs部分のみ実行したい場合
./cloud-run-jobs/deploy-job.sh deploy
```

### 📚 プログラムからの利用

他のスクリプトから共通関数を利用：

```bash
#!/bin/bash
# 共通関数の読み込み
source "./cloud-run-jobs/job-functions.sh"

# ジョブのデプロイ
deploy_cloud_run_job_with_yaml "job.yaml" "asia-northeast1"

# ジョブの実行
execute_cloud_run_job "my-job" "asia-northeast1"

# ジョブの実行履歴確認
get_job_executions "my-job" "asia-northeast1" 5
```

## 設定のカスタマイズ

### 環境変数での設定

以下の環境変数で設定をカスタマイズできます：

| 環境変数 | デフォルト値 | 説明 |
|---------|-------------|------|
| `PROJECT_ID` | gcloud設定値 | Google CloudプロジェクトID |
| `JOB_NAME` | anpi-call-create-task-job | Cloud Run Job名 |
| `REGION` | asia-northeast1 | デプロイリージョン |
| `ENVIRONMENT` | development | 実行環境 |
| `LOG_LEVEL` | debug | ログレベル |
| `CPU` | 1 | CPUリソース |
| `MEMORY` | 512Mi | メモリリソース |
| `TASK_TIMEOUT` | 300 | タスクタイムアウト（秒） |
| `MAX_RETRIES` | 1 | 最大リトライ回数 |

### 設定ファイルでの設定

`job-config.env`ファイルを編集してデフォルト値を変更：

```bash
# 設定ファイルを編集
vi ./cloud-run-jobs/job-config.env

# 設定を読み込んでデプロイ
source ./cloud-run-jobs/job-config.env
./cloud-run-jobs/deploy-job.sh deploy
```

## 実行例

### 開発環境でのデプロイ

```bash
# 開発環境設定でデプロイ
ENVIRONMENT=development LOG_LEVEL=debug ./cloud-run-jobs/deploy-job.sh deploy

# 手動実行でテスト
./cloud-run-jobs/deploy-job.sh execute

# ログ確認
./cloud-run-jobs/deploy-job.sh logs
```

### 本番環境でのデプロイ

```bash
# 本番環境設定でデプロイ
ENVIRONMENT=production \
LOG_LEVEL=info \
JOB_NAME=anpi-call-scheduler-prod \
CPU=2 \
MEMORY=1Gi \
TASK_TIMEOUT=600 \
./cloud-run-jobs/deploy-job.sh deploy
```

## トラブルシューティング

### よくある問題

#### ジョブのデプロイに失敗する

```bash
# 設定の確認
gcloud config list

# 権限の確認
gcloud auth list

# Cloud Build権限の確認
gcloud projects get-iam-policy $(gcloud config get-value project)
```

#### ジョブの実行に失敗する

```bash
# ログの詳細確認
./cloud-run-jobs/deploy-job.sh logs

# 実行履歴の確認
./cloud-run-jobs/deploy-job.sh status

# ジョブ設定の確認
gcloud run jobs describe $JOB_NAME --region=$REGION
```

## 関連ドキュメント

- [../docs/deployment.md](../docs/deployment.md) - 全体のデプロイ手順
- [../docs/gcp-resources.md](../docs/gcp-resources.md) - GCPリソース仕様
- [../docs/troubleshooting.md](../docs/troubleshooting.md) - トラブルシューティング
