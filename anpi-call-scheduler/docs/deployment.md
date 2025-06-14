# デプロイメント手順

## デプロイメント概要

このシステムは以下のGCPサービスを使用してデプロイされます：

- **Cloud Build**: CI/CDパイプライン
- **Container Registry**: Dockerイメージストレージ
- **Cloud Run Jobs**: バッチ処理実行環境
- **Cloud Scheduler**: 定時実行スケジューラー

## 自動デプロイ（推奨）

### 1. 標準デプロイ

```bash
# 一括デプロイ実行
./deploy-complete.sh
```

このスクリプトは以下の処理を自動実行します：

1. 必要なAPIの有効化確認
2. Cloud Build権限の設定
3. Cloud Tasksキューの作成
4. Cloud Buildによるイメージビルド・デプロイ
5. Cloud Schedulerの設定
6. 動作確認テスト

### 2. 設定カスタマイズデプロイ

環境変数を指定してデプロイ：

```bash
# カスタム設定でデプロイ
ENVIRONMENT=production LOG_LEVEL=info ./deploy-complete.sh
```

## 手動デプロイ

### 1. イメージビルド

```bash
# Dockerイメージをビルド
docker build -t gcr.io/$PROJECT_ID/anpi-call-scheduler:latest .

# イメージをプッシュ
docker push gcr.io/$PROJECT_ID/anpi-call-scheduler:latest
```

### 2. Cloud Run Jobデプロイ

```bash
# Cloud Run Jobを作成/更新
gcloud run jobs deploy anpi-call-scheduler-dev \
    --image=gcr.io/$PROJECT_ID/anpi-call-scheduler:latest \
    --region=asia-northeast1 \
    --cpu=1 \
    --memory=512Mi \
    --task-timeout=300 \
    --max-retries=1 \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=development,LOG_LEVEL=debug
```

### 3. Cloud Schedulerの設定

推奨方法：
```bash
# 共通関数を使用した統一的な設定
./cloud-scheduler/deploy-scheduler.sh
```

手動設定（参考）：

```bash
# 既存のスケジューラーを削除（存在する場合）
gcloud scheduler jobs delete anpi-call-scheduler-dev-hourly \
    --location=asia-northeast1 \
    --quiet

# スケジューラーを作成
gcloud scheduler jobs create http anpi-call-scheduler-dev-hourly \
    --location=asia-northeast1 \
    --schedule="0 * * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/anpi-call-scheduler-dev:run" \
    --http-method=POST \
    --oidc-service-account-email="$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --max-retry-attempts=1
```

## Cloud Buildを使用したCI/CD

### cloudbuild.yamlの構成

```yaml
steps:
  # 1. Dockerイメージビルド
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/anpi-call-scheduler:latest', '.']
  
  # 2. イメージプッシュ
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/anpi-call-scheduler:latest']

  # 3. Cloud Run Jobデプロイ
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'jobs'
      - 'deploy'
      - '${_JOB_NAME}'
      - '--image=gcr.io/$PROJECT_ID/anpi-call-scheduler:latest'
      - '--region=${_REGION}'
      - '--cpu=${_CPU}'
      - '--memory=${_MEMORY}'
      - '--task-timeout=${_TASK_TIMEOUT}'
      - '--max-retries=${_MAX_RETRIES}'
      - '--set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=${_ENVIRONMENT},LOG_LEVEL=${_LOG_LEVEL}'
```

### Cloud Buildトリガーの設定

```bash
# GitHubリポジトリと連携したトリガーを作成
gcloud builds triggers create github \
    --repo-name=anpi-call-scheduler \
    --repo-owner=YOUR_GITHUB_USERNAME \
    --branch-pattern=main \
    --build-config=cloudbuild.yaml \
    --substitutions=_JOB_NAME=anpi-call-scheduler-dev,_REGION=asia-northeast1
```

## 環境別デプロイ戦略

### 開発環境

```bash
# 開発環境用の設定
export ENVIRONMENT=development
export JOB_NAME=anpi-call-scheduler-dev
export LOG_LEVEL=debug
export SCHEDULE="0 * * * *"  # 毎時実行

./deploy.sh
```

### ステージング環境

```bash
# ステージング環境用の設定
export ENVIRONMENT=staging
export JOB_NAME=anpi-call-scheduler-staging
export LOG_LEVEL=info
export SCHEDULE="0 */2 * * *"  # 2時間ごと実行

./deploy.sh
```

### 本番環境

```bash
# 本番環境用の設定
export ENVIRONMENT=production
export JOB_NAME=anpi-call-scheduler-prod
export LOG_LEVEL=warning
export SCHEDULE="0 * * * *"  # 毎時実行
export CPU=2
export MEMORY=1Gi
export TASK_TIMEOUT=600
export MAX_RETRIES=3

./deploy.sh
```

## デプロイ後の確認

### 1. デプロイ成功確認

```bash
# Cloud Run Jobの存在確認
gcloud run jobs describe $JOB_NAME --region=$REGION

# Cloud Schedulerの状態確認
gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION
```

### 2. テスト実行

```bash
# 手動実行テスト
gcloud run jobs execute $JOB_NAME --region=$REGION

# スケジューラーテスト
gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION
```

### 3. ログ確認

```bash
# 実行ログの確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)"
```

## ロールバック手順

### 前のバージョンに戻す

```bash
# 利用可能なイメージを確認
gcloud container images list-tags gcr.io/$PROJECT_ID/anpi-call-scheduler

# 特定のイメージでデプロイ
gcloud run jobs update $JOB_NAME \
    --image=gcr.io/$PROJECT_ID/anpi-call-scheduler:PREVIOUS_TAG \
    --region=$REGION
```

### 緊急時の処理停止

```bash
# スケジューラーを一時停止
gcloud scheduler jobs pause $SCHEDULER_NAME --location=$REGION

# 実行中のジョブを確認
gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --filter="status.completionTime=''"
```

## トラブルシューティング

### デプロイエラーの確認

```bash
# 最新のビルドログを確認
BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")
gcloud builds log $BUILD_ID

# Cloud Run Jobのエラー確認
gcloud run jobs describe $JOB_NAME --region=$REGION --format="yaml(status)"
```

### 権限エラーの解決

```bash
# Cloud Buildサービスアカウントに権限を付与
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser"
```
