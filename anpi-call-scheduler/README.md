# ANPI Call Scheduler

安否確認コール システムのスケジューラー。データベースからユーザーの通話スケジュール設定を取得し、Cloud Tasks にタスクを登録します。

## プロジェクト概要

### 機能

- MySQL（Cloud SQL）データベースからユーザーの通話設定を取得
- 曜日と時間に基づいてタスクの実行日時を計算
- Google Cloud Tasks にタスクを登録
- Cloud Run Jobs としてスケジュール実行
- Cloud Scheduler による定期実行（毎時0分）

### システム構成

- **Cloud Scheduler**: 毎時0分に Cloud Run Job をトリガー
- **Cloud Run Job**: Python バッチ処理でスケジュール計算・タスク登録
- **Cloud SQL**: ユーザー情報と通話設定を格納
- **Cloud Tasks**: 個別の安否確認タスクをキューイング
- **外部連携**: Twilio サービスによる音声通話実行

### 処理の流れ

1. **定時実行**: Cloud Scheduler が毎時0分に Cloud Run Job をトリガー
2. **データ取得**: usersテーブルから通話設定（曜日・時刻）を取得
3. **スケジュール計算**: 各ユーザーの次回通話日時を計算
4. **タスク登録**: Cloud Tasks に個別の安否確認タスクを登録
5. **通話実行**: 指定時刻にTwilioサービスがWebhook経由で通話実行

詳細な処理フローは [📋 処理フロー詳細](docs/processing-flow.md) を参照してください。

## プロジェクト構成

```
anpi-call-scheduler/
├── main.py                      # メインのバッチ処理アプリケーション
├── Dockerfile                   # Dockerイメージ定義
├── requirements.txt             # Python依存関係
├── job.yaml                     # Cloud Run Job設定
│
├── deploy-complete.sh           # 完全自動デプロイスクリプト（推奨）
├── setup-scheduler.sh           # Cloud Scheduler 設定専用
├── deploy-application.sh        # アプリケーションデプロイ
├── setup-infrastructure.sh     # インフラ設定
│
├── cloudbuild.yaml             # Cloud Build設定
├── test_db_connection.py       # データベース接続テスト
│
├── docs/                       # ドキュメント
│   ├── processing-flow.md      # 処理フロー詳細
│   ├── setup-guide.md          # セットアップ手順
│   ├── deployment.md           # デプロイ手順
│   ├── gcp-resources.md        # GCPリソース仕様
│   ├── external-systems.md     # 外部システム接続情報
│   ├── system-architecture.md  # システム構成詳細
│   └── troubleshooting.md      # トラブルシューティング
│
└── README.md                   # このファイル
```

### 主要ファイル

| ファイル名 | 用途 | 説明 |
|-----------|------|------|
| `main.py` | アプリケーション | バッチ処理のメインロジック |
| `job.yaml` | Cloud Run Job設定 | リソース制限、環境変数、接続設定 |
| `deploy-complete.sh` | 完全デプロイ | 全工程を自動化する統合スクリプト |
| `setup-scheduler.sh` | Scheduler設定 | Cloud Scheduler の作成・管理専用 |
| `Dockerfile` | コンテナ | Dockerイメージビルド設定 |
| `requirements.txt` | 依存関係 | Python パッケージ定義 |

## 実行方法

### 🚀 クイックスタート（推奨）

完全自動デプロイで全工程を一括実行：

```bash
# 全設定を自動化
./deploy-complete.sh
```

このスクリプトは以下をすべて自動実行します：
1. 必要なAPIの有効化
2. Cloud Tasksキューの作成
3. Docker イメージのビルド・プッシュ
4. Cloud Run Job のデプロイ
5. サービスアカウント権限の設定
6. Cloud Scheduler の作成・設定
7. 動作確認テスト

### 個別実行

#### 1. インフラストラクチャセットアップ（初回のみ）

```bash
# 必要なAPI、IAM権限、Cloud Tasksキューを作成
./setup-infrastructure.sh
```

#### 2. アプリケーションデプロイ

```bash
# Cloud Run JobとCloud Schedulerをデプロイ
./deploy-application.sh
```

#### 3. Cloud Scheduler のみ設定

```bash
# Cloud Scheduler のみ作成・設定
./setup-scheduler.sh
```

### 動作確認

#### 手動実行テスト

```bash
# Cloud Run Job手動実行
gcloud run jobs execute anpi-call-create-task-job --region=asia-northeast1

# Cloud Scheduler手動実行
gcloud scheduler jobs run anpi-call-scheduler-job --location=asia-northeast1
```

#### 実行状況確認

```bash
# 実行履歴確認
gcloud run jobs executions list --job=anpi-call-create-task-job --region=asia-northeast1 --limit=5

# 作成されたタスクの確認
gcloud tasks list --queue=anpi-call-queue --location=asia-northeast1

# ログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-create-task-job" --limit=20
```

### 管理コマンド

```bash
# スケジューラー状態確認
gcloud scheduler jobs describe anpi-call-scheduler-job --location=asia-northeast1

# スケジューラー削除
gcloud scheduler jobs delete anpi-call-scheduler-job --location=asia-northeast1

# Job詳細確認
gcloud run jobs describe anpi-call-create-task-job --region=asia-northeast1

# キュー状態確認
gcloud tasks queues describe anpi-call-queue --location=asia-northeast1
```

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | - |
| `CLOUD_TASKS_LOCATION` | Cloud Tasksのロケーション | `asia-northeast1` |
| `CLOUD_TASKS_QUEUE` | Cloud Tasksキュー名 | `anpi-call-queue` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `DB_HOST` | データベースホスト | - |
| `DB_USER` | データベースユーザー | `default` |
| `DB_PASSWORD` | データベースパスワード | - |
| `DB_NAME` | データベース名 | `default` |
| `ANPI_CALL_URL` | 安否確認サービスURL | Twilio Webhook URL |

## ドキュメント

詳細は `docs/` フォルダを参照：

- [📋 処理フロー詳細](docs/processing-flow.md) - システムの処理フロー図と詳細説明
- [⚙️ セットアップ手順](docs/setup-guide.md) - 環境構築の詳細手順
- [🚀 デプロイ手順](docs/deployment.md) - デプロイメント詳細ガイド
- [☁️ GCPリソース仕様](docs/gcp-resources.md) - 使用するGCPリソースの詳細
- [🔗 外部システム連携](docs/external-systems.md) - Twilio等の外部システム情報
- [🏗️ システム構成](docs/system-architecture.md) - アーキテクチャ詳細
- [🛠️ トラブルシューティング](docs/troubleshooting.md) - よくある問題と解決方法