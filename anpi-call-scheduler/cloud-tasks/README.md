# Cloud Tasks - 安否確認コールシステム

本ディレクトリは、安否確認コールシステムで使用するCloud Tasksキューの作成・管理を行う専用ツール集です。

## ディレクトリ構成

```
cloud-tasks/
├── tasks-functions.sh        # Cloud Tasks 共通関数ライブラリ
├── deploy-cloud-tasks.sh    # Cloud Tasks管理スクリプト（統合コマンド）
├── tasks-config.yaml        # Cloud Tasks設定定義
└── README.md                # このファイル
```

## 主要ファイル

| ファイル名 | 用途 | 説明 |
|-----------|------|------|
| `tasks-functions.sh` | 共通関数 | キュー作成・管理・状態確認などの再利用可能な関数 |
| `deploy-cloud-tasks.sh` | 管理スクリプト | デプロイ・状態確認・管理操作の統合コマンド |
| `tasks-config.yaml` | 設定定義 | キューの設定値を一元管理 |

## 使用方法

### 🚀 クイックセットアップ（推奨）

Cloud Tasksキューを自動作成：

```bash
# Cloud Tasks管理スクリプトでデプロイ
./cloud-tasks/deploy-cloud-tasks.sh deploy
```

### 📋 管理コマンド

新しい管理スクリプトを使用して各種操作を実行：

```bash
# キューのデプロイ
./cloud-tasks/deploy-cloud-tasks.sh deploy

# キューの状態確認
./cloud-tasks/deploy-cloud-tasks.sh status

# キュー内のタスク一覧表示
./cloud-tasks/deploy-cloud-tasks.sh list

# キューの一時停止
./cloud-tasks/deploy-cloud-tasks.sh pause

# キューの再開
./cloud-tasks/deploy-cloud-tasks.sh resume

# ヘルプ表示
./cloud-tasks/deploy-cloud-tasks.sh help
```

### 🔧 環境変数設定

環境変数で設定をカスタマイズ：

```bash
# 環境変数の設定例
export CLOUD_TASKS_LOCATION="asia-northeast1"
export CLOUD_TASKS_QUEUE="my-custom-queue"
export MAX_CONCURRENT_DISPATCHES=50
export MAX_ATTEMPTS=5

# デプロイ実行
./cloud-tasks/deploy-cloud-tasks.sh deploy
```

### 🔗 メインデプロイスクリプトとの統合

`deploy-complete.sh`からは自動的にこのディレクトリの機能が呼び出されます：

```bash
# メインデプロイスクリプトの実行
./deploy-complete.sh

# Cloud Tasks部分のみ実行したい場合
./cloud-tasks/deploy-cloud-tasks.sh deploy
```

### 📚 プログラムからの利用

他のスクリプトから共通関数を利用：

```bash
#!/bin/bash
# 共通関数の読み込み
source "./cloud-tasks/tasks-functions.sh"

# キューの作成
create_cloud_tasks_queue "$PROJECT_ID" "asia-northeast1" "my-queue"

# キューの状態確認
check_tasks_queue_status "my-queue" "asia-northeast1"

# タスク一覧表示
list_tasks_in_queue "my-queue" "asia-northeast1" 10
```

## 設定のカスタマイズ

### 環境変数での設定

以下の環境変数で設定をカスタマイズできます：

| 環境変数 | デフォルト値 | 説明 |
|---------|-------------|------|
| `PROJECT_ID` | gcloud設定値 | Google CloudプロジェクトID |
| `CLOUD_TASKS_LOCATION` | asia-northeast1 | Cloud Tasksのロケーション |
| `CLOUD_TASKS_QUEUE` | anpi-call-queue | キュー名 |
| `MAX_CONCURRENT_DISPATCHES` | 100 | 最大並列実行数 |
| `MAX_RETRY_DURATION` | 3600s | 最大リトライ期間 |
| `MAX_ATTEMPTS` | 3 | 最大試行回数 |
| `MIN_BACKOFF` | 10s | 最小バックオフ時間 |
| `MAX_BACKOFF` | 300s | 最大バックオフ時間 |
| `ENVIRONMENT` | development | 環境名 |
| `LOG_LEVEL` | info | ログレベル |

### 設定例

```bash
# カスタム設定でセットアップ
export CLOUD_TASKS_QUEUE="my-custom-queue"
export MAX_CONCURRENT_DISPATCHES=50
export MAX_ATTEMPTS=5

./cloud-tasks/deploy-cloud-tasks.sh deploy
```

## 動作確認

### 手動確認コマンド

```bash
# キューの詳細確認
gcloud tasks queues describe anpi-call-queue --location=asia-northeast1

# キュー内のタスク確認
gcloud tasks list --queue=anpi-call-queue --location=asia-northeast1 --limit=10

# キューの状態確認（関数使用）
source ./cloud-tasks/tasks-functions.sh
check_tasks_queue_status "anpi-call-queue" "asia-northeast1"
```

### タスク作成テスト

```bash
# テスト用タスクの作成
gcloud tasks create-http-task test-task-$(date +%s) \
    --queue=anpi-call-queue \
    --location=asia-northeast1 \
    --url=https://httpbin.org/post \
    --method=POST \
    --header="Content-Type=application/json" \
    --body-content='{"test": "message", "timestamp": "'$(date -Iseconds)'"}'
```

## 管理コマンド

### キュー管理

```bash
# キューの一覧表示
gcloud tasks queues list --location=asia-northeast1

# キューの詳細確認
gcloud tasks queues describe anpi-call-queue --location=asia-northeast1

# キューの一時停止
gcloud tasks queues pause anpi-call-queue --location=asia-northeast1

# キューの再開
gcloud tasks queues resume anpi-call-queue --location=asia-northeast1

# キューの削除（注意：すべてのタスクが削除されます）
gcloud tasks queues delete anpi-call-queue --location=asia-northeast1
```

### タスク管理

```bash
# タスクの一覧表示
gcloud tasks list --queue=anpi-call-queue --location=asia-northeast1

# 個別タスクの詳細確認
gcloud tasks describe TASK_NAME --queue=anpi-call-queue --location=asia-northeast1

# タスクの削除
gcloud tasks delete TASK_NAME --queue=anpi-call-queue --location=asia-northeast1
```

## トラブルシューティング

### よくある問題

1. **APIが無効**: Cloud Tasks APIの有効化が必要
2. **権限エラー**: Cloud Tasks Admin権限が必要
3. **キューが見つからない**: 先にキューを作成する必要があります

詳細は [../docs/troubleshooting.md](../docs/troubleshooting.md) を参照してください。

## 統合ポイント

このCloud Tasksセットアップは以下のスクリプトから呼び出されます：

- `../setup-infrastructure.sh` - インフラストラクチャ初期セットアップ時
- `../deploy-complete.sh` - 完全デプロイメント時
- `../deploy-application.sh` - アプリケーションデプロイ時

使用例：
```bash
# 他のスクリプトから呼び出し
source "./cloud-tasks/tasks-functions.sh"
create_cloud_tasks_queue "$PROJECT_ID" "$REGION" "$CLOUD_TASKS_QUEUE"
```

## 関連ドキュメント

- [📋 処理フロー詳細](../docs/processing-flow.md)
- [🚀 デプロイ手順](../docs/deployment.md)
- [🛠️ セットアップガイド](../docs/setup-guide.md)
- [🔧 トラブルシューティング](../docs/troubleshooting.md)

---

## サポート

- 詳細なドキュメント: `../docs/`
- 問題報告: GitHubのIssues
- 設定例: `tasks-config.yaml`
