# AnpiCall メール送信システム

Cloud Functions + SendGrid を使用したHTTPトリガー型メール送信システムです。

## 📋 概要

このシステムは、Google Cloud Functions 上で動作するサーバーレスメール送信サービスです。HTTPリクエストを受信してSendGrid APIを使用してメールを送信します。

### システム構成

```
HTTPリクエスト → Cloud Functions (HTTPトリガー) → SendGrid API → メール送信
```

### 主な機能

- 🚀 サーバーレス型メール送信
- 📧 HTML/テキストメール対応
- 🔒 CORS対応でWebアプリケーションから利用可能
- ⚡ 高可用性・自動スケーリング
- 🛡️ エラーハンドリング完備

## 📁 ディレクトリ構成

```
anpi-call-mail/
├── main.py              # Cloud Functions メイン処理
├── requirements.txt     # Python依存関係定義
├── deploy.sh           # GCPデプロイスクリプト
├── simple_test.py      # ローカルテスト用スクリプト
├── README.md           # プロジェクト説明（このファイル）
├── .env.example        # 環境変数設定例
├── .env                # 環境変数設定（ローカル開発用）
├── .gcloudignore       # GCPデプロイ時の除外設定
└── .gitignore          # Git管理除外設定
```

## 🚀 デプロイ方法

### 1. 前提条件

- Google Cloud Platform アカウント
- `gcloud` CLI がインストール・認証済み
- SendGrid アカウントとAPIキーを取得済み

### 2. SendGrid APIキー取得

1. [SendGrid](https://sendgrid.com/) にサインアップ
2. Settings > API Keys でAPIキーを作成
3. 権限を「Mail Send」に設定

### 3. GCPプロジェクト設定

```bash
# GCPプロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4. デプロイ実行

```bash
# リポジトリをクローン
git clone <repository-url>
cd anpi-call-mail

# デプロイスクリプトを実行
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

## 🧪 動作確認方法

### curl を使用したテスト

デプロイ後に表示されるFunction URLを使用してテストします：

```bash
# 基本的なメール送信テスト
curl -X POST "YOUR_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "テストメール",
    "content": "<h1>Hello from AnpiCall!</h1><p>This is a test email.</p>"
  }'
```

### Pythonスクリプトでのテスト

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

### ローカル環境での動作確認

#### 1. 環境設定

まず、`.env.example`を参考に`.env`ファイルを作成します：

```bash
# .env.exampleをコピーして.envファイルを作成
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# SENDGRID_API_KEY=SG.xxxx を実際のAPIキーに変更
```

#### 2. 依存関係のインストール

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt
```

#### 3. シンプルテストスクリプトでの確認

```bash
# 設定値をテストして実際にメール送信
python simple_test.py
```

#### 4. Functions Framework でのローカルテスト

```bash
# Functions Framework でローカル実行
functions-framework --target=send_email --debug

# 別ターミナルでテスト
curl -X POST "http://localhost:8080" \
  -H "Content-Type: application/json" \
  -d '{"to_email": "test@example.com", "subject": "Test", "content": "Hello"}'
```

#### 5. 環境変数の確認

設定が正しく読み込まれているかを確認するには：

```bash
# 環境変数が正しく設定されているかチェック
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SENDGRID_API_KEY:', '***' + os.getenv('SENDGRID_API_KEY', 'NOT_SET')[-4:])
print('FROM_EMAIL:', os.getenv('FROM_EMAIL', 'NOT_SET'))
print('TO_EMAIL:', os.getenv('TO_EMAIL', 'NOT_SET'))
"
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

### リクエスト例

#### 最小構成
```json
{
  "to_email": "recipient@example.com",
  "subject": "件名",
  "content": "メール本文"
}
```

#### 完全指定
```json
{
  "to_email": "recipient@example.com",
  "to_name": "受信者名",
  "subject": "件名",
  "content": "<html><body><h1>HTMLメール</h1></body></html>",
  "from_email": "sender@example.com",
  "from_name": "送信者名"
}
```

## ⚙️ 設定

### 環境変数

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|-------------|------|
| `SENDGRID_API_KEY` | SendGrid APIキー | なし | ✅ |
| `FROM_EMAIL` | 送信元メールアドレス | なし | ✅ |
| `TO_EMAIL` | 送信先メールアドレス（テスト用） | なし | ✅ |
| `FROM_NAME` | 送信者名 | `AnpiCall安否確認システム` | ❌ |
| `TO_NAME` | 受信者名（テスト用） | `テストユーザー` | ❌ |

### 環境変数の設定例

`.env.example` ファイルを参考に`.env`ファイルを作成してください：

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集
# AnpiCall システム設定ファイル

# SendGrid API設定
SENDGRID_API_KEY=SG.your-actual-api-key-here

# メール設定
FROM_EMAIL=your-email@example.com
TO_EMAIL=recipient@example.com
FROM_NAME=AnpiCall安否確認システム
TO_NAME=テストユーザー
```

#### ローカル開発での設定手順

1. **設定ファイルの準備**
```bash
# リポジトリをクローン後
cd anpi-call-mail

# 設定ファイルをコピー
cp .env.example .env

# エディタで.envファイルを編集
nano .env  # または vi .env
```

2. **必要な設定値の更新**
- `SENDGRID_API_KEY`: SendGridで取得したAPIキー
- `FROM_EMAIL`: 送信者のメールアドレス（SendGridで認証済み）
- `TO_EMAIL`: テスト送信先のメールアドレス

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
gcloud functions logs read send-email --region=asia-northeast1 --limit=50
```

##  参考資料

- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [Google Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Cloud Functions Python Runtime](https://cloud.google.com/functions/docs/concepts/python-runtime)

## ⚠️ 重要な注意事項

### 送信者認証について

実際にメールを送信するには、SendGridで送信者認証が必要です：

1. **Single Sender Verification（推奨）**
   - SendGrid Dashboard > Settings > Sender Authentication
   - Single Sender Verification を選択
   - 送信者メールアドレスを認証

2. **Domain Authentication（本格運用時）**
   - 独自ドメインを使用する場合
   - DNS設定が必要

### Sandbox Modeについて

開発・テスト時はSandbox Modeの使用を推奨します。実際のメール送信は行われず、SendGrid側でテスト処理されます。

---

このシステムは、シンプルで信頼性の高いメール送信サービスを提供します。ご質問やサポートが必要な場合は、プロジェクトの管理者にお問い合わせください。
