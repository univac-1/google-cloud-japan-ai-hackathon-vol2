# GCP メール送信システム (AnpiCall)

Cloud Functions + SendGrid を使用したHTTPトリガー型メール送信システムです。

## 📋 システム構成

```
HTTPリクエスト → Cloud Functions (HTTPトリガー) → SendGrid API → メール送信
```

## 🚀 クイックスタート

### 1. 前提条件

- Python 3.12+
- GCP プロジェクトが作成済み
- `gcloud` CLI がインストール・認証済み
- SendGrid アカウントとAPIキーを取得済み

### 2. SendGrid APIキー取得

1. [SendGrid](https://sendgrid.com/) にサインアップ
2. Settings > API Keys でAPIキーを作成
3. 権限を「Mail Send」に設定

### 3. ローカル開発環境のセットアップ

```bash
# 環境設定
./setup_local.sh

# ローカルサーバー起動
./local_server.py

# 別ターミナルでテスト実行
./test_email.py http://localhost:8080
```

### 4. GCPへのデプロイ

```bash
# APIキーを指定してデプロイ
./deploy.sh "YOUR_SENDGRID_API_KEY"

# または、ダミーキーでテストデプロイ（後で更新）
./deploy.sh
```

### 5. APIキーの更新（本番環境）

```bash
gcloud functions deploy send-email \
  --update-env-vars SENDGRID_API_KEY=YOUR_REAL_API_KEY \
  --region=asia-northeast1
```

### 6. 統合テスト

```bash
# ローカル+クラウド統合テスト
export FUNCTION_URL="YOUR_DEPLOYED_FUNCTION_URL"
./run_tests.py
```

### 7. Docker を使用した開発

```bash
# Docker Composeでサービスを起動
docker-compose up --build

# テスト実行
docker-compose --profile test run email-tester

# サービス停止
docker-compose down
```

## 📡 API仕様

### エンドポイント
- **URL**: Cloud Functions のデプロイ後に表示されるURL
- **Method**: POST
- **Content-Type**: application/json

### リクエスト形式

```json
{
  "to_email": "recipient@example.com",    // 必須: 送信先メールアドレス
  "to_name": "受信者名",                   // オプション: 送信先名前
  "subject": "件名",                      // 必須: メール件名
  "content": "<h1>メール本文</h1>",        // 必須: メール本文（HTML可）
  "from_email": "sender@example.com",     // オプション: 送信元（環境変数で設定可）
  "from_name": "送信者名"                 // オプション: 送信者名（環境変数で設定可）
}
```

### レスポンス形式

#### 成功時 (200)
```json
{
  "message": "Email sent successfully",
  "success": true,
  "sendgrid_response": {
    "status_code": 202,
    "message_id": "xxxx-xxxx-xxxx"
  }
}
```

#### エラー時 (400/500)
```json
{
  "error": "エラーメッセージ",
  "success": false
}
```

## 🧪 テスト

### curlでのテスト

```bash
# デプロイ後に表示されるURLを使用
curl -X POST "YOUR_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "テストメール",
    "content": "<h1>Hello from AnpiCall!</h1><p>This is a test email.</p>"
  }'
```

### Pythonでのテスト

```python
import requests
import json

url = "YOUR_FUNCTION_URL"
data = {
    "to_email": "test@example.com",
    "subject": "テストメール from Python",
    "content": "<h1>Hello!</h1><p>Pythonからのテストメールです。</p>"
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## ⚙️ 設定

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `SENDGRID_API_KEY` | SendGrid APIキー | なし（必須） |
| `DEFAULT_FROM_EMAIL` | デフォルト送信元メールアドレス | `noreply@example.com` |
| `DEFAULT_FROM_NAME` | デフォルト送信者名 | `AnpiCall System` |

### Cloud Functions 設定

- **Runtime**: Python 3.12
- **Memory**: 256MB
- **Timeout**: 60秒
- **Region**: asia-northeast1 (東京)
- **Trigger**: HTTP (認証不要)

## 🔒 セキュリティ

### 本番環境での推奨設定

1. **Secret Manager の使用**
```bash
# APIキーをSecret Managerに保存
gcloud secrets create sendgrid-api-key --data-file=-
echo "YOUR_API_KEY" | gcloud secrets create sendgrid-api-key --data-file=-

# Cloud Functions に権限付与
gcloud secrets add-iam-policy-binding sendgrid-api-key \
  --member="serviceAccount:YOUR_PROJECT@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

2. **認証の追加**
```bash
# 認証を要求するようにデプロイ
gcloud functions deploy send-email \
  --no-allow-unauthenticated \
  --region=asia-northeast1
```

3. **IPアドレス制限**
- Cloud Armor または VPC Service Controls を使用

## 🐛 トラブルシューティング

### よくあるエラー

1. **"SENDGRID_API_KEY environment variable not set"**
   - APIキーが設定されていません
   - `deploy.sh` でAPIキーを指定してデプロイしてください

2. **"Content-Type must be application/json"**
   - リクエストヘッダーに `Content-Type: application/json` を設定してください

3. **"Missing required fields"**
   - `to_email`, `subject`, `content` は必須フィールドです

### ログの確認

```bash
# Cloud Functions のログを確認
gcloud functions logs read send-email --region=asia-northeast1
```

## 📊 モニタリング

### Cloud Monitoring での監視項目

- 実行回数
- エラー率
- 実行時間
- メモリ使用量

### アラート設定例

```bash
# エラー率が5%を超えた場合のアラート
gcloud alpha monitoring policies create \
  --policy-from-file=alert-policy.yaml
```

## 🔄 アップデート

```bash
# 新しいバージョンをデプロイ
./deploy.sh "YOUR_SENDGRID_API_KEY"

# 特定の環境変数のみ更新
gcloud functions deploy send-email \
  --update-env-vars SENDGRID_API_KEY=NEW_API_KEY \
  --region=asia-northeast1
```

## 🛠️ 開発ツール

### ファイル構成

```
anpi-call-mail/
├── main.py              # メイン関数（Cloud Functions用）
├── local_server.py      # ローカル開発サーバー
├── requirements.txt     # Python依存関係
├── deploy.sh           # GCPデプロイスクリプト
├── setup_local.sh      # ローカル環境セットアップ
├── test_email.py       # APIテストスクリプト
├── run_tests.py        # 統合テストスクリプト
├── docker-compose.yml  # Docker設定
├── Dockerfile          # Dockerイメージ定義
├── .env.example        # 環境変数の例
└── README.md           # このファイル
```

### 開発ワークフロー

1. **ローカル開発**: `./local_server.py` でローカルテスト
2. **単体テスト**: `./test_email.py` でAPI動作確認
3. **統合テスト**: `./run_tests.py` で全体テスト
4. **デプロイ**: `./deploy.sh` でGCP展開
5. **本番テスト**: 実際のFunction URLでテスト

## 📚 参考資料

- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Cloud Functions Python Runtime](https://cloud.google.com/functions/docs/concepts/python-runtime)
