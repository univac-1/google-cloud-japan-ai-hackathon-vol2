# トラブルシューティング

## よくある問題と解決方法

### デプロイ関連

#### 問題: deploy.shでエラーが発生する

**症状:**
```
エラー: .env ファイルが見つかりません
```

**原因:** 設定ファイル（.env）が存在しない

**解決方法:**
```bash
# .envファイルを作成
cp .env.example .env
# 設定値を編集
vi .env
```

**症状:**
```
ERROR: gcloud crashed (AttributeError): module 'collections' has no attribute 'Mapping'
```

**原因:** Google Cloud SDKのバージョンが古い

**解決方法:**
```bash
# Google Cloud SDKをアップデート
gcloud components update
```

#### 問題: Cloud Buildでビルドが失敗する

**症状:**
```
Step #0 - "Build": ERROR: failed to solve: dockerfile parse error
```

**原因:** Dockerfileの構文エラー

**解決方法:**
```bash
# Dockerfileの構文チェック
docker build -t test-image .

# 問題箇所を特定して修正
```

**症状:**
```
ERROR: (gcloud.builds.submit) PERMISSION_DENIED: The caller does not have permission
```

**原因:** Cloud Buildサービスアカウントの権限不足

**解決方法:**
```bash
# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Cloud Buildサービスアカウントに権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.developer"
```

### Cloud Run Jobs関連

#### 問題: ジョブの実行が失敗する

**症状:**
```
Error: The request failed with status code: 500
```

**原因:** アプリケーションの内部エラー

**解決方法:**
```bash
# ジョブのログを確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-scheduler-dev" \
  --limit=50 --format="table(timestamp,severity,textPayload)"

# 詳細なエラー情報を取得
gcloud run jobs executions describe EXECUTION_NAME \
  --region=asia-northeast1 \
  --format="value(status.conditions[0].message)"
```

**症状:**
```
Error: Job execution timed out
```

**原因:** ジョブのタイムアウト時間を超過

**解決方法:**
```bash
# ジョブのタイムアウト時間を延長
gcloud run jobs replace job.yaml \
  --region=asia-northeast1
```

job.yamlでタイムアウト設定を調整：
```yaml
spec:
  template:
    spec:
      taskTimeout: 7200s  # 2時間に延長
```

#### 問題: ジョブが実行されない

**症状:** Cloud Schedulerは正常だが、ジョブが起動しない

**原因:** Cloud Schedulerの権限設定

**解決方法:**
```bash
# Cloud Schedulerサービスアカウントの確認
gcloud iam service-accounts list --filter="displayName~scheduler"

# Cloud Run呼び出し権限を付与
gcloud run jobs add-iam-policy-binding anpi-call-scheduler-dev \
  --region=asia-northeast1 \
  --member="serviceAccount:scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 外部API接続関連

#### 問題: 安否確認システムAPIに接続できない

**症状:**
```
ConnectionError: HTTPSConnectionPool(host='api.anpi-system.example.com', port=443)
```

**原因:** ネットワーク接続またはDNS解決の問題

**解決方法:**
```bash
# DNS解決確認
nslookup api.anpi-system.example.com

# ネットワーク接続確認
curl -I https://api.anpi-system.example.com/v1/health

# Cloud Runからの外部接続確認
gcloud run jobs execute anpi-call-scheduler-dev \
  --region=asia-northeast1 \
  --args="curl,-I,https://api.anpi-system.example.com/v1/health"
```

**症状:**
```
HTTP 401 Unauthorized
```

**原因:** API認証の問題

**解決方法:**
```bash
# Secret Managerの値確認
gcloud secrets versions access latest --secret="anpi-api-key"

# APIキーの有効性テスト
curl -H "Authorization: Bearer $(gcloud secrets versions access latest --secret=anpi-api-key)" \
     https://api.anpi-system.example.com/v1/health
```

### データベース接続関連

#### 問題: Cloud SQLに接続できない

**症状:**
```
Error 2003 (HY000): Can't connect to MySQL server
```

**原因:** Cloud SQL認証またはネットワーク設定

**解決方法:**
```bash
# Cloud SQLインスタンスの状態確認
gcloud sql instances describe employee-db-instance

# サービスアカウントの権限確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

**症状:**
```
Access denied for user 'anpi-call-scheduler-sa'
```

**原因:** データベースユーザーの設定問題

**解決方法:**
```bash
# IAMユーザーを作成
gcloud sql users create anpi-call-scheduler-sa@{PROJECT_ID}.iam \
  --instance=employee-db-instance \
  --type=cloud_iam_service_account

# データベース権限を付与
mysql -h {CLOUD_SQL_IP} -u root -p << EOF
GRANT SELECT, INSERT, UPDATE ON employee_db.* TO 'anpi-call-scheduler-sa'@'%';
FLUSH PRIVILEGES;
EOF
```

### 監視・ログ関連

#### 問題: ログが出力されない

**症状:** Cloud Loggingにアプリケーションログが表示されない

**原因:** ログ設定またはサービスアカウント権限

**解決方法:**
```bash
# ログ出力権限確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --filter="bindings.role:roles/logging.logWriter"

# 権限が無い場合は付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

#### 問題: メトリクスが取得できない

**症状:** Cloud Monitoringでメトリクスが表示されない

**解決方法:**
```bash
# Monitoring API有効化確認
gcloud services list --enabled --filter="name:monitoring.googleapis.com"

# 有効化されていない場合
gcloud services enable monitoring.googleapis.com

# メトリクス書き込み権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

### パフォーマンス関連

#### 問題: 処理が遅い

**症状:** ジョブ実行時間が長い

**診断方法:**
```bash
# 実行時間の確認
gcloud run jobs executions list \
  --job=anpi-call-scheduler-dev \
  --region=asia-northeast1 \
  --format="table(name,startTime,completionTime)"

# リソース使用量確認
gcloud logging read "resource.type=cloud_run_job AND jsonPayload.message~memory" \
  --limit=20
```

**解決方法:**
1. CPU/メモリリソースの増加
```yaml
# job.yamlで設定変更
spec:
  template:
    spec:
      template:
        spec:
          containers:
          - resources:
              limits:
                cpu: "2"      # 1→2に増加
                memory: "1Gi" # 512Mi→1Giに増加
```

2. 並列処理の実装
```python
# main.pyで並列処理を追加
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def process_employees_parallel(employee_list, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_employee, emp) for emp in employee_list]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return results
```

## エラーコード一覧

| エラーコード | 説明 | 対応方法 |
|-------------|------|----------|
| ERR_001 | 設定ファイル読み込みエラー | .envファイルの存在・内容確認 |
| ERR_002 | API認証エラー | Secret Managerの認証情報確認 |
| ERR_003 | データベース接続エラー | Cloud SQL設定・権限確認 |
| ERR_004 | 外部API接続タイムアウト | ネットワーク・API側状況確認 |
| ERR_005 | Pub/Sub送信エラー | トピック・権限設定確認 |

## デバッグモード

開発時のデバッグに useful な設定：

### 環境変数設定
```bash
# 詳細ログ出力
export LOG_LEVEL=DEBUG

# ローカル実行モード
export ENVIRONMENT=local

# テストデータ使用
export USE_TEST_DATA=true
```

### ローカル実行

```bash
# ローカルでの動作確認
python main.py

# Docker環境での確認
docker build -t anpi-scheduler-local .
docker run --env-file .env anpi-scheduler-local
```

## サポート情報

### 緊急時連絡先

| レベル | 対象 | 連絡先 | 対応時間 |
|--------|------|--------|----------|
| P0 | システム全体停止 | on-call@company.com | 24時間365日 |
| P1 | 一部機能不全 | dev-team@company.com | 平日 9:00-18:00 |
| P2 | パフォーマンス問題 | tech-support@company.com | 平日 10:00-17:00 |

### ログ分析コマンド集

```bash
# エラーログのみ抽出
gcloud logging read "resource.type=cloud_run_job AND severity>=ERROR" --limit=50

# 特定時間範囲のログ
gcloud logging read "resource.type=cloud_run_job AND timestamp>=\"2025-01-15T10:00:00Z\"" --limit=50

# 実行IDでフィルタ
gcloud logging read "resource.type=cloud_run_job AND jsonPayload.execution_id=\"exec-12345\"" --limit=50

# パフォーマンス関連ログ
gcloud logging read "resource.type=cloud_run_job AND jsonPayload.message~\"処理時間\"" --limit=20
```

### 健全性チェックスクリプト

```bash
#!/bin/bash
# health-check.sh
echo "=== 安否確認システム健全性チェック ==="

# 1. Cloud Run Jobs状態確認
echo "1. Cloud Run Jobs確認..."
gcloud run jobs describe anpi-call-scheduler-dev --region=asia-northeast1 --format="value(status.conditions[0].status)"

# 2. 最新実行結果確認
echo "2. 最新実行結果確認..."
gcloud run jobs executions list --job=anpi-call-scheduler-dev --region=asia-northeast1 --limit=1 --format="value(status.conditions[0].status)"

# 3. API接続確認
echo "3. 外部API接続確認..."
curl -s -o /dev/null -w "%{http_code}" https://api.anpi-system.example.com/v1/health

# 4. データベース接続確認
echo "4. データベース接続確認..."
gcloud sql instances describe employee-db-instance --format="value(state)"

echo "健全性チェック完了"
```
