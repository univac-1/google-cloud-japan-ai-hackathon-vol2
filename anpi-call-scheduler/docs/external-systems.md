# 外部システム接続情報

本システムが接続する外部システムとの連携仕様を記載します。

## 接続システム概要

| システム名 | 用途 | 接続方法 | 認証方式 |
|------------|------|----------|----------|
| 安否確認システム | 安否情報の取得・更新 | REST API | API Key |
| 通知システム | アラート送信 | HTTP Webhook | Bearer Token |
| 社員データベース | 社員情報取得 | Cloud SQL | IAM認証 |
| ログ分析システム | ログ転送 | Cloud Pub/Sub | サービスアカウント |

## 安否確認システム

### 接続情報

| 項目 | 設定値 | 確認方法 |
|------|--------|----------|
| エンドポイント | `https://api.anpi-system.example.com/v1` | システム管理者に確認 |
| API Key | Secret Manager: `anpi-api-key` | `gcloud secrets versions access latest --secret="anpi-api-key"` |
| タイムアウト | 30秒 | アプリケーション設定 |
| リトライ回数 | 3回 | アプリケーション設定 |

### API仕様

#### 社員安否情報取得

```http
GET /employees/{employee_id}/safety-status
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

**レスポンス例:**
```json
{
  "employee_id": "EMP001",
  "status": "safe|unsafe|unknown",
  "last_updated": "2025-01-15T10:00:00Z",
  "location": {
    "latitude": 35.6762,
    "longitude": 139.6503
  }
}
```

#### 安否確認要求送信

```http
POST /safety-check-requests
Authorization: Bearer {API_KEY}
Content-Type: application/json

{
  "employee_ids": ["EMP001", "EMP002"],
  "message": "安否確認をお願いします",
  "priority": "high|normal|low",
  "deadline": "2025-01-15T18:00:00Z"
}
```

### エラーハンドリング

| HTTPステータス | 説明 | 対応 |
|----------------|------|------|
| 401 | 認証エラー | API Keyを確認 |
| 429 | レート制限 | 指数バックオフでリトライ |
| 500 | サーバーエラー | ログ出力後、管理者に通知 |

### 接続確認方法

```bash
# API接続テスト
curl -H "Authorization: Bearer $(gcloud secrets versions access latest --secret=anpi-api-key)" \
     https://api.anpi-system.example.com/v1/health

# 期待レスポンス
# {"status": "ok", "version": "1.0.0"}
```

## 通知システム

### 接続情報

| 項目 | 設定値 | 確認方法 |
|------|--------|----------|
| Webhook URL | Secret Manager: `notification-webhook-url` | `gcloud secrets versions access latest --secret="notification-webhook-url"` |
| 認証Token | Secret Manager: `notification-token` | `gcloud secrets versions access latest --secret="notification-token"` |
| チャンネル | `#emergency-alerts` | 通知システム管理者に確認 |

### Webhook仕様

```http
POST {WEBHOOK_URL}
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "channel": "#emergency-alerts",
  "message": "緊急: 安否確認処理でエラーが発生しました",
  "severity": "critical|warning|info",
  "timestamp": "2025-01-15T10:00:00Z",
  "source": "anpi-call-scheduler"
}
```

### 接続確認方法

```bash
# 通知テスト
curl -X POST \
  -H "Authorization: Bearer $(gcloud secrets versions access latest --secret=notification-token)" \
  -H "Content-Type: application/json" \
  -d '{"channel":"#test","message":"接続テスト","severity":"info"}' \
  $(gcloud secrets versions access latest --secret=notification-webhook-url)
```

## 社員データベース (Cloud SQL)

### 接続情報

| 項目 | 設定値 | 確認方法 |
|------|--------|----------|
| インスタンス名 | `employee-db-instance` | `gcloud sql instances list` |
| データベース名 | `employee_db` | `gcloud sql databases list --instance=employee-db-instance` |
| 接続方式 | Cloud SQL Proxy | プライベートIP接続 |
| 認証方式 | IAM認証 | サービスアカウント |

### データベーススキーマ

#### employeesテーブル

```sql
CREATE TABLE employees (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(50),
    position VARCHAR(50),
    emergency_contact VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### safety_statusテーブル

```sql
CREATE TABLE safety_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(10) NOT NULL,
    status ENUM('safe', 'unsafe', 'unknown') DEFAULT 'unknown',
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### 接続確認方法

```bash
# Cloud SQL Proxyを起動
cloud_sql_proxy -instances={PROJECT_ID}:asia-northeast1:employee-db-instance=tcp:3306 &

# 接続テスト
mysql -h 127.0.0.1 -P 3306 -u anpi-call-scheduler-sa@{PROJECT_ID}.iam -p employee_db
```

### よく使用するクエリ

```sql
-- アクティブな社員一覧取得
SELECT id, name, email, phone 
FROM employees 
WHERE is_active = TRUE;

-- 未確認の社員一覧取得
SELECT e.id, e.name, e.email 
FROM employees e 
LEFT JOIN safety_status s ON e.id = s.employee_id 
WHERE e.is_active = TRUE 
  AND (s.status IS NULL OR s.status = 'unknown' OR s.last_checked < NOW() - INTERVAL 24 HOUR);
```

## ログ分析システム (Cloud Pub/Sub)

### 接続情報

| 項目 | 設定値 | 確認方法 |
|------|--------|----------|
| トピック名 | `anpi-logs` | `gcloud pubsub topics list` |
| サブスクリプション | `log-analysis-sub` | `gcloud pubsub subscriptions list` |
| メッセージ形式 | JSON | アプリケーション仕様 |

### メッセージスキーマ

```json
{
  "timestamp": "2025-01-15T10:00:00Z",
  "level": "INFO|WARN|ERROR",
  "source": "anpi-call-scheduler",
  "message": "処理完了: 対象社員数 150名",
  "execution_id": "exec-12345",
  "metadata": {
    "processed_count": 150,
    "success_count": 148,
    "error_count": 2
  }
}
```

### 接続確認方法

```bash
# トピック存在確認
gcloud pubsub topics describe anpi-logs

# テストメッセージ送信
gcloud pubsub topics publish anpi-logs \
  --message='{"test": "connection", "timestamp": "'$(date -Iseconds)'"}'

# サブスクリプションでメッセージ受信確認
gcloud pubsub subscriptions pull log-analysis-sub --auto-ack --limit=1
```

## 環境別設定

### 開発環境

- 安否確認システム: `https://dev-api.anpi-system.example.com/v1`
- データベース: `employee-db-dev`
- Pub/Subトピック: `anpi-logs-dev`

### 本番環境

- 安否確認システム: `https://api.anpi-system.example.com/v1`
- データベース: `employee-db-prod`
- Pub/Subトピック: `anpi-logs`

## トラブルシューティング

### よくある接続問題

#### API接続エラー

```bash
# DNS解決確認
nslookup api.anpi-system.example.com

# ネットワーク接続確認
curl -I https://api.anpi-system.example.com/v1/health

# 認証確認
gcloud secrets versions access latest --secret="anpi-api-key"
```

#### データベース接続エラー

```bash
# Cloud SQL接続確認
gcloud sql instances describe employee-db-instance

# IAM権限確認
gcloud projects get-iam-policy {PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com"
```

#### Pub/Sub接続エラー

```bash
# トピック権限確認
gcloud pubsub topics get-iam-policy anpi-logs

# サービスアカウント権限付与
gcloud pubsub topics add-iam-policy-binding anpi-logs \
  --member="serviceAccount:anpi-call-scheduler-sa@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

## 連絡先

システム連携に関する問い合わせ先：

| システム | 担当者 | 連絡先 | 営業時間 |
|----------|--------|--------|----------|
| 安否確認システム | システム管理者 | admin@anpi-system.example.com | 平日 9:00-18:00 |
| 通知システム | IT部門 | it-support@company.example.com | 24時間365日 |
| データベース | DBA チーム | dba@company.example.com | 平日 9:00-18:00 |
| Pub/Sub | インフラチーム | infra@company.example.com | 24時間365日 |

## 変更履歴

| 日付 | 変更内容 | 担当者 |
|------|----------|--------|
| 2025-01-15 | 初版作成 | システム開発チーム |
