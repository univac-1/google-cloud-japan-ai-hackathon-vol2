# ANPI Call Scheduler

安否確認コール システムのスケジューラー。データベースからユーザーの通話設定を取得し、現在時刻に基づいて即座に実行すべき安否確認を判定してCloud Tasksにタスクを作成します。

## プロジェクト概要

### 機能

- MySQL（Cloud SQL）データベースからユーザーの通話設定を取得
- 現在時刻と設定された曜日・時間を比較して即時実行判定
- Google Cloud Tasks に即時実行タスクを作成
- Cloud Run Jobs として定期実行
- Cloud Scheduler による定期実行（15分間隔または設定間隔）

### システム構成

- **Cloud Scheduler**: 定期的に Cloud Run Job をトリガー（推奨：15分間隔実行）
- **Cloud Run Job**: Python バッチ処理で即時実行判定・タスク作成
- **Cloud SQL**: ユーザー情報と通話設定を格納
- **Cloud Tasks**: 個別の安否確認タスクをキューイング
- **外部連携**: Twilio サービスによる音声通話実行

### 処理の流れ

1. **現在時刻チェック**: データベースから全ユーザーの通話設定を取得
2. **即時実行判定**: 現在時刻と各ユーザーの設定（曜日・時刻）を比較
3. **許容時間内確認**: 指定時刻の前後5分以内（設定可能）かを判定
4. **即時タスク作成**: 条件に一致するユーザーのCloud Tasksタスクを即座に作成
5. **通話実行**: 作成されたタスクによりTwilioサービスがWebhook経由で通話実行

**即時実行専用設計**: このアプリケーションは将来のスケジューリング機能を持たず、現在時刻に基づく即時実行のみを行います。定期的な実行により適切なタイミングでの安否確認を実現します。

詳細な処理フローは [📋 処理フロー詳細](docs/processing-flow.md) を参照してください。

## プロジェクト構成

```
anpi-call-scheduler/
├── deploy-complete.sh           # 統合デプロイスクリプト（推奨）
│
├── cloud-run-jobs/              # Cloud Run Jobs専用ディレクトリ
│   ├── main.py                  # バッチ処理アプリケーション
│   ├── Dockerfile               # Cloud Run Jobs用Dockerイメージ
│   ├── requirements.txt         # Python依存関係
│   ├── cloudbuild.yaml          # Cloud Build設定
│   ├── job.yaml                 # Cloud Run Job設定
│   ├── deploy-job.sh            # Cloud Run Jobs専用デプロイ
│   ├── job-functions.sh         # 共通関数ライブラリ
│   ├── job-config.env           # ジョブ設定
│   └── README.md                # Cloud Run Jobs使用方法
│
├── cloud-scheduler/             # Cloud Scheduler設定
│   ├── scheduler-functions.sh   # 共通関数ライブラリ
│   ├── deploy-scheduler.sh      # Cloud Scheduler専用デプロイ
│   ├── scheduler.yaml           # スケジューラー設定定義
│   └── README.md                # Cloud Scheduler使用方法
│
├── cloud-tasks/                 # Cloud Tasks設定
│   ├── tasks-functions.sh      # 共通関数ライブラリ
│   ├── deploy-cloud-tasks.sh   # Cloud Tasks専用デプロイ
│   ├── tasks-config.yaml       # キュー設定定義
│   └── README.md               # Cloud Tasks使用方法
│
├── scripts/                    # 開発・テスト用ユーティリティ
│   ├── test_db_connection.py   # データベース接続テスト
│   ├── add_test_data.py        # テストデータ追加
│   ├── add_test_data.sql       # SQLテストデータ
│   ├── add_current_time_test_data.py # 現在時刻テストデータ
│   ├── add_bulk_test_data.py   # 大量テストデータ追加
│   ├── check_db_schema.py      # スキーマ確認
│   ├── debug_immediate_execution.py # デバッグ用
│   ├── cloud-sql-proxy         # Cloud SQL Proxyバイナリ
│   └── README.md               # スクリプト使用方法
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
| `cloud-run-jobs/main.py` | アプリケーション | バッチ処理のメインロジック |
| `cloud-run-jobs/deploy-job.sh` | Cloud Run Jobs | ジョブのデプロイ・管理専用スクリプト |
| `deploy-complete.sh` | 完全デプロイ | 全工程を自動化する統合スクリプト |
| `cloud-scheduler/deploy-scheduler.sh` | Scheduler設定 | Cloud Scheduler の作成・管理専用 |
| `cloud-run-jobs/Dockerfile` | コンテナ | Cloud Run Jobs用Dockerイメージ |
| `cloud-run-jobs/requirements.txt` | 依存関係 | Python パッケージ定義 |
| `scripts/test_db_connection.py` | 開発・テスト | データベース接続テスト用スクリプト |

## 実行方法

### 🚀 クイックスタート（推奨）

完全自動デプロイで全工程を一括実行：

```bash
# 完全自動デプロイ（推奨）
./deploy-complete.sh

# 本番環境での自動デプロイ
./deploy-complete.sh --production

# インフラストラクチャのみセットアップ
./deploy-complete.sh --infrastructure-only

# アプリケーションのみデプロイ
./deploy-complete.sh --deploy-only

# テストをスキップしてデプロイ
./deploy-complete.sh --skip-test
```

統合デプロイスクリプトは以下をすべて自動実行します：
1. 必要なAPIの有効化
2. Cloud Tasksキューの作成
3. Cloud Run Jobs のビルド・デプロイ
4. サービスアカウント権限の設定
5. Cloud Scheduler の作成・設定
6. 動作確認テスト

### 個別実行

#### 1. Cloud Run Jobs のみデプロイ

```bash
# Cloud Run Jobs 単体デプロイ
./cloud-run-jobs/deploy-job.sh deploy

# または Cloud Build を使用
./cloud-run-jobs/deploy-job.sh build

# ジョブの手動実行
./cloud-run-jobs/deploy-job.sh execute

# ジョブの管理（ログ確認、削除など）
./cloud-run-jobs/deploy-job.sh logs
./cloud-run-jobs/deploy-job.sh status
```

#### 2. Cloud Scheduler のみ設定

```bash
# Cloud Scheduler のみ作成・設定（推奨）
./cloud-scheduler/deploy-scheduler.sh
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

### 開発・テスト用スクリプト

開発・テスト・デバッグ用のスクリプトは `scripts/` フォルダに整理されています：

```bash
# データベース接続テスト
python scripts/test_db_connection.py

# 現在時刻に近いテストデータを追加
python scripts/add_current_time_test_data.py

# 即時実行機能のデバッグ
python scripts/debug_immediate_execution.py

# 大量テストデータの追加
python scripts/add_bulk_test_data.py
```

詳細は [scripts/README.md](scripts/README.md) を参照してください。

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | - |
| `CLOUD_TASKS_LOCATION` | Cloud Tasksのロケーション | `asia-northeast1` |
| `CLOUD_TASKS_QUEUE` | Cloud Tasksキュー名 | `anpi-call-queue` |
| `IMMEDIATE_CALL_TOLERANCE_MINUTES` | 即時実行の許容時間（分） | `5` |
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