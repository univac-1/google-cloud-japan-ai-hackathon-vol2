# ANPI Call Scheduler

安否確認コール システムのスケジューラー。データベースからユーザーの通話スケジュール設定を取得し、Cloud Tasks にタスクを登録します。

## 機能

- PostgreSQLデータベースからユーザーの通話設定を取得
- 曜日と時間に基づいてタスクの実行日時を計算
- Google Cloud Tasks にタスクを登録
- Cloud Run Jobs としてスケジュール実行

## 開発環境

### VS Code DevContainer を使用する場合（推奨）

1. VS Code で Dev Containers 拡張機能をインストール
2. このフォルダを VS Code で開く
3. "Reopen in Container" を選択
4. 環境変数ファイルを設定：
   ```bash
   cp .env.local .env
   # .env ファイルを編集して実際の値を設定
   ```

### ローカル環境で直接実行する場合

1. Python 3.11+ をインストール
2. 開発環境をセットアップ：
   ```bash
   ./dev-setup.sh
   ```
3. アプリケーションを実行：
   ```bash
   python main.py
   ```

## 環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | `my-project-123` |
| `DB_HOST` | データベースホスト | `10.0.0.1` |
| `DB_PORT` | データベースポート | `5432` |
| `DB_USER` | データベースユーザー | `postgres` |
| `DB_NAME` | データベース名 | `anpi_db` |
| `DB_PASSWORD` | データベースパスワード | `secret123` |
| `QUEUE_NAME` | Cloud Tasks キュー名 | `anpi-call-queue` |
| `LOCATION` | Cloud Tasks リージョン | `asia-northeast1` |

## プロジェクト構成

```
anpi-call-scheduler/
├── main.py                        # メインのバッチ処理
├── Dockerfile                     # Dockerイメージ定義
├── requirements.txt               # Python依存関係
├── setup-infrastructure.sh       # インフラセットアップスクリプト
├── deploy-application.sh          # Cloud Buildデプロイスクリプト
├── deploy-local.sh               # ローカルDockerビルド & デプロイスクリプト
├── cloudbuild.yaml               # Cloud Build設定
├── job.yaml                      # Cloud Run Job設定
├── .devcontainer/                # 開発環境設定
│   ├── devcontainer.json         # VS Code devcontainer設定
│   ├── Dockerfile.dev            # 開発用Dockerfile
│   └── docker-compose.yml        # ローカル開発用Docker Compose
├── docs/                         # ドキュメント
└── README.md                     # このファイル
```

## 開発環境セットアップ

### Option 1: VS Code devcontainer（推奨）

1. VS Codeでこのフォルダを開く
2. 「Reopen in Container」を選択
3. devcontainerが自動的にセットアップされます

### Option 2: ローカルDocker Compose

```bash
cd .devcontainer
docker-compose up -d
docker-compose exec anpi-scheduler bash
```

## デプロイ手順

### ローカルビルド & デプロイ（推奨 - 高速）

```bash
# 高速デプロイ（ローカルでDockerビルド）
./deploy-local.sh
```

この方式では：
- Dockerイメージをローカルでビルド
- Container Registryにプッシュ
- Cloud Run Jobをデプロイ
- Cloud Schedulerを設定

### Cloud Buildデプロイ（従来方式）

```bash
# Cloud Buildでのデプロイ（時間がかかる場合あり）
./deploy-application-cloudbuild.sh
```

## 実行手順

### 1. 初期設定
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth login
```

### 2. インフラストラクチャセットアップ（初回のみ）
```bash
# 必要なAPI、IAM権限、Cloud Tasksキューを作成
./setup-infrastructure.sh
```

### 3. アプリケーションデプロイ（開発時に繰り返し実行）
```bash
# Cloud Run JobとCloud Schedulerをデプロイ
./deploy-application.sh
```

### 4. 手動実行とテスト

#### Cloud Run Jobの手動実行
```bash
# Job名: anpi-call-create-task-job
gcloud run jobs execute anpi-call-create-task-job --region=asia-northeast1
```

#### Cloud Schedulerの手動実行
```bash
# Scheduler名: anpi-call-scheduler-job  
gcloud scheduler jobs run anpi-call-scheduler-job --location=asia-northeast1
```

#### 実行状況の確認
```bash
# 実行履歴の確認
gcloud run jobs executions list --job=anpi-call-create-task-job --region=asia-northeast1 --limit=5

# 実行詳細の確認
gcloud run jobs executions describe [EXECUTION_NAME] --region=asia-northeast1

# ログの確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-create-task-job" --limit=20
```

#### Cloud Tasksの確認
```bash
# 作成されたタスクの確認
gcloud tasks list --queue=anpi-call-queue --location=asia-northeast1
```

### 5. スケジュール設定

デフォルトでは毎時0分に実行されます（cron: `0 * * * *`）。
設定を変更する場合は`.env`ファイルの`SCHEDULE`を編集してください。

#### Cloud Scheduler作成時の注意事項

Cloud Run Jobsを実行するSchedulerではOAuth認証を使用してください：

```bash
# 正しいScheduler作成方法 (OAuth認証)
gcloud scheduler jobs create http anpi-call-scheduler-job \
  --location=asia-northeast1 \
  --schedule="0 * * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/univac-aiagent/jobs/anpi-call-create-task-job:run" \
  --http-method=POST \
  --oauth-service-account-email="894704565810-compute@developer.gserviceaccount.com" \
  --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
  --max-retry-attempts=1 \
  --min-backoff=10s \
  --max-backoff=60s

# 手動実行テスト
gcloud scheduler jobs run anpi-call-scheduler-job --location=asia-northeast1

# 実行状況確認
gcloud scheduler jobs describe anpi-call-scheduler-job --location=asia-northeast1
```

#### 認証方式について

- ✅ **OAuth Token**: Cloud Run Jobsとの互換性が良い（推奨）
- ❌ **OIDC Token**: Cloud Run Jobsで認証エラーが発生する可能性

### 6. トラブルシューティング

#### Cloud Schedulerのエラー確認
```bash
# Scheduler状況確認
gcloud scheduler jobs describe anpi-call-scheduler-job --location=asia-northeast1

# エラーがある場合は status.code が表示される
# code: 16 = UNAUTHENTICATED (認証エラー)
```

#### Cloud Run Job実行の確認
```bash
# 実行履歴確認
gcloud run jobs executions list --job=anpi-call-create-task-job --region=asia-northeast1 --limit=5

# Cloud Tasksタスク確認
gcloud tasks list --queue=anpi-call-queue --location=asia-northeast1

# ログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-create-task-job" --limit=10
```

## 環境変数

必要な環境変数:
- `GOOGLE_CLOUD_PROJECT`: GCPプロジェクトID
- `CLOUD_TASKS_LOCATION`: Cloud Tasksのロケーション（デフォルト: asia-northeast1）
- `CLOUD_TASKS_QUEUE`: Cloud Tasksキュー名（デフォルト: anpi-call-queue）
- `LOG_LEVEL`: ログレベル（DEBUG/INFO/WARNING/ERROR）

## ドキュメント

詳細は `docs/` フォルダを参照：
- [setup-guide.md](docs/setup-guide.md) - セットアップ手順
- [deployment.md](docs/deployment.md) - デプロイ手順
- [gcp-resources.md](docs/gcp-resources.md) - GCPリソース仕様
- [external-systems.md](docs/external-systems.md) - 外部システム接続情報
- [troubleshooting.md](docs/troubleshooting.md) - トラブルシューティング