# Cloud Scheduler - 安否確認コールスケジューラー

このディレクトリには、安否確認コールスケジューラーのCloud Scheduler関連の設定とスクリプトが含まれています。

## ファイル構成

| ファイル名 | 用途 | 説明 |
|-----------|------|------|
| `scheduler-functions.sh` | 共通関数ライブラリ | Cloud Scheduler作成処理の共通関数 |
| `deploy-scheduler.sh` | デプロイスクリプト | Cloud Schedulerの作成・更新（推奨） |
| `scheduler.yaml` | 設定ファイル | スケジューラーの設定値定義 |
| `README.md` | ドキュメント | このファイル |

## スケジューラー設定

設定内容は以下のファイルを参照してください：

- **設定値**: [`scheduler.yaml`](./scheduler.yaml) - スケジューラー名、実行スケジュール、タイムゾーン等
- **デプロイ設定**: [`deploy-scheduler.sh`](./deploy-scheduler.sh) - プロジェクト設定、リージョン、サービスアカウント等

### 実行フロー

1. **定期実行**: 毎分Cloud Schedulerがトリガー（即時実行対応）
2. **HTTP POST**: Cloud Run JobのAPI エンドポイントを呼び出し
3. **即時判定**: Cloud Run Jobで現在時刻に基づく即時実行対象者の判定
4. **タスク作成**: 対象者に対して即座にCloud Tasksタスクを作成
5. **通話実行**: Cloud Tasksキューから即座に実行

## 使用方法

### 🚀 クイックデプロイ（推奨）

```bash
# Cloud Schedulerを作成・デプロイ
./cloud-scheduler/deploy-scheduler.sh
```

### 共通関数の使用

他のスクリプトから共通関数を使用する場合：

```bash
# 共通関数の読み込み
source "./cloud-scheduler/scheduler-functions.sh"

# OIDC認証でCloud Schedulerを作成
create_cloud_scheduler "$PROJECT_ID" "$REGION" "$SCHEDULER_NAME" "$JOB_NAME" "$SCHEDULE" "$TIMEZONE" "$SERVICE_ACCOUNT"

# OAuth認証でCloud Schedulerを作成（互換性）
create_cloud_scheduler_oauth "$PROJECT_ID" "$REGION" "$SCHEDULER_NAME" "$JOB_NAME" "$SCHEDULE" "$TIMEZONE" "$SERVICE_ACCOUNT"

# スケジューラーの状態確認
check_scheduler_status "$SCHEDULER_NAME" "$REGION"

# スケジューラーのテスト実行
test_scheduler "$SCHEDULER_NAME" "$REGION"
```

### 個別実行

```bash
# 共通関数の単体テスト
./cloud-scheduler/scheduler-functions.sh
```

## 動作確認

設定されたスケジューラーの確認方法については [`scheduler.yaml`](./scheduler.yaml) の設定値を参照してください。

### 手動実行テスト

```bash
# スケジューラーの手動実行（スケジューラー名は scheduler.yaml を参照）
gcloud scheduler jobs run $(grep scheduler_name scheduler.yaml | cut -d'"' -f4) --location=$(grep location scheduler.yaml | cut -d'"' -f4)
```

### 状態確認

```bash
# スケジューラーの詳細確認
gcloud scheduler jobs describe $(grep scheduler_name scheduler.yaml | cut -d'"' -f4) --location=$(grep location scheduler.yaml | cut -d'"' -f4)

# 実行履歴確認
gcloud scheduler jobs list --location=$(grep location scheduler.yaml | cut -d'"' -f4)
```

### ログ確認

```bash
# Cloud Run Jobのログ確認（ジョブ名は scheduler.yaml を参照）
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$(grep job_name scheduler.yaml | cut -d'"' -f4)" \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)"
```

## スケジュール変更

スケジュールを変更する場合は、以下のファイルを編集してください：

1. **設定ファイル**: [`scheduler.yaml`](./scheduler.yaml) の `schedule` 値を変更
2. **デプロイスクリプト**: [`deploy-scheduler.sh`](./deploy-scheduler.sh) の `SCHEDULE` 変数を変更

```bash
# 例: 30分ごとに実行
schedule: "*/30 * * * *"

# 例: 平日9-17時の毎時実行  
schedule: "0 9-17 * * 1-5"

# 例: 毎日午前9時に実行
schedule: "0 9 * * *"
```

## 管理コマンド

各種管理コマンドで使用する設定値は [`scheduler.yaml`](./scheduler.yaml) を参照してください。

### スケジューラー管理

```bash
# スケジューラー一覧（リージョンは scheduler.yaml を参照）
gcloud scheduler jobs list --location=$(grep location scheduler.yaml | cut -d'"' -f4)

# スケジューラー詳細
gcloud scheduler jobs describe $(grep scheduler_name scheduler.yaml | cut -d'"' -f4) --location=$(grep location scheduler.yaml | cut -d'"' -f4)

# スケジューラー削除
gcloud scheduler jobs delete $(grep scheduler_name scheduler.yaml | cut -d'"' -f4) --location=$(grep location scheduler.yaml | cut -d'"' -f4)
```

### 権限管理

```bash
# サービスアカウント権限確認（サービスアカウントは scheduler.yaml を参照）
gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$(grep service_account scheduler.yaml | cut -d'"' -f4)"
```

## トラブルシューティング

### よくある問題

1. **権限エラー**: サービスアカウントにCloud Run Invoker権限が必要
2. **ジョブが見つからない**: 先にCloud Run Jobをデプロイする必要があります
3. **APIが無効**: Cloud Scheduler APIの有効化が必要

詳細は [../docs/troubleshooting.md](../docs/troubleshooting.md) を参照してください。

## 関連ドキュメント

- [📋 処理フロー詳細](../docs/processing-flow.md)
- [🚀 デプロイ手順](../docs/deployment.md)
- [🛠️ セットアップガイド](../docs/setup-guide.md)
- [🔧 トラブルシューティング](../docs/troubleshooting.md)
