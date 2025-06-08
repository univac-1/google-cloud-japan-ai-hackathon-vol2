# GCPリソース仕様

## 使用サービス一覧

本システムで使用するGCPサービスとそのリソース仕様を記載します。

## Cloud Run Jobs

### リソース仕様

| 項目 | 設定値 | 説明 |
|------|--------|------|
| リージョン | asia-northeast1 | 東京リージョン |
| CPU | 1 | vCPU数 |
| メモリ | 512Mi | メモリ容量 |
| 最大並列実行数 | 1 | 同時実行可能なタスク数 |
| タスクタイムアウト | 3600s | 1時間でタイムアウト |
| 最大再試行回数 | 3 | 失敗時の再試行回数 |

### ジョブ名

- **開発環境**: `anpi-call-scheduler-dev`
- **本番環境**: `anpi-call-scheduler-prod`

### サービスアカウント

- 名前: `anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com`
- 権限:
  - Cloud SQL Client
  - Cloud Storage Object Viewer
  - Cloud Logging Writer
  - Secret Manager Secret Accessor

## Cloud Scheduler

### スケジュール設定

| 項目 | 設定値 | 説明 |
|------|--------|------|
| スケジュール名 | anpi-call-scheduler-cron | スケジューラー名 |
| Cron表記 | `0 */1 * * *` | 毎時0分に実行 |
| タイムゾーン | Asia/Tokyo | 日本時間 |
| ターゲット | Cloud Run Jobs | 実行対象 |

## Container Registry / Artifact Registry

### イメージリポジトリ

- **Container Registry**: `gcr.io/{PROJECT_ID}/anpi-call-scheduler`
- **Artifact Registry**: `{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPOSITORY}/anpi-call-scheduler`

### タグ戦略

- `latest`: 最新のビルド
- `dev-{TIMESTAMP}`: 開発環境用
- `prod-{VERSION}`: 本番環境用（セマンティックバージョニング）

## Cloud Build

### ビルド設定

| 項目 | 設定値 |
|------|--------|
| 設定ファイル | cloudbuild.yaml |
| トリガー | 手動実行 |
| マシンタイプ | e2-standard-2 |
| タイムアウト | 600s |

### 必要な権限

Cloud Buildサービスアカウントに以下の権限が必要：

- Cloud Run Developer
- Service Account User
- Container Registry Service Agent

## 環境変数

### 共通環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| GOOGLE_CLOUD_PROJECT | プロジェクトID | my-project-id |
| CLOUD_RUN_JOB | ジョブ名 | anpi-call-scheduler-dev |
| ENVIRONMENT | 実行環境 | development / production |
| LOG_LEVEL | ログレベル | INFO |

### 環境別設定

環境別の設定は`.env`ファイルで管理：

```bash
# 開発環境
PROJECT_ID=my-project-dev
ENVIRONMENT=development
REGION=asia-northeast1
JOB_NAME=anpi-call-scheduler-dev

# 本番環境
PROJECT_ID=my-project-prod
ENVIRONMENT=production
REGION=asia-northeast1
JOB_NAME=anpi-call-scheduler-prod
```

## リソース確認コマンド

### Cloud Run Jobs

```bash
# ジョブ一覧確認
gcloud run jobs list --region=asia-northeast1

# ジョブ詳細確認
gcloud run jobs describe anpi-call-scheduler-dev --region=asia-northeast1

# 実行履歴確認
gcloud run jobs executions list --job=anpi-call-scheduler-dev --region=asia-northeast1
```

### Cloud Scheduler

```bash
# スケジューラー一覧確認
gcloud scheduler jobs list

# スケジューラー詳細確認
gcloud scheduler jobs describe anpi-call-scheduler-cron --location=asia-northeast1
```

### Container Registry

```bash
# イメージ一覧確認
gcloud container images list --repository=gcr.io/{PROJECT_ID}

# イメージタグ確認
gcloud container images list-tags gcr.io/{PROJECT_ID}/anpi-call-scheduler
```

## 監視・ログ

### Cloud Logging

ログ確認クエリ：

```bash
# アプリケーションログ
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-scheduler-dev" --limit=50

# エラーログのみ
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-scheduler-dev AND severity>=ERROR" --limit=20
```

### Cloud Monitoring

メトリクス確認：

- ジョブ実行回数
- 実行時間
- 成功/失敗率
- CPU/メモリ使用率

## セキュリティ設定

### IAM設定

最小権限の原則に従い、必要最小限の権限のみを付与：

```bash
# サービスアカウント作成
gcloud iam service-accounts create anpi-call-scheduler-sa \
    --display-name="安否確認スケジューラーサービスアカウント"

# 必要な権限を付与
gcloud projects add-iam-policy-binding {PROJECT_ID} \
    --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

### Secret Manager

機密情報はSecret Managerで管理：

```bash
# シークレット作成例
gcloud secrets create db-password --data-file=password.txt

# Cloud Runからのアクセス権限付与
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```
