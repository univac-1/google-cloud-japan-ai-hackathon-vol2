# Twilio Voice + OpenAI Realtime API アウトバウンド通話システム

## 概要

このプロジェクトは、TwilioのVoice APIとOpenAIのRealtime APIを組み合わせて、AIアシスタントによるアウトバウンド通話を実現するシステムです。

### 主な機能
- AIアシスタントからの自動発信
- リアルタイム音声認識・応答
- 日本語での自然な会話
- WebSocket通信による低遅延音声処理

## ディレクトリ構成

```
anpi-call-twilio-outbound/
├── .env                 # 環境変数設定ファイル
├── .gitignore          # Git除外設定
├── README.md           # プロジェクト説明書
├── main.py             # メインアプリケーション
├── requirements.txt    # Python依存関係
└── venv/              # Python仮想環境
```

## 前提条件

- Python 3.12以上
- Twilioアカウントと電話番号
- OpenAI API キー（Realtime API利用可能）
- ngrok（ローカル開発用）

## セットアップ手順

### 1. 依存関係のインストール

```bash
# 仮想環境の作成・有効化
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

## デプロイメント

### Cloud Run への自動デプロイ

```bash
# 環境変数を設定してデプロイ
export OPENAI_API_KEY="your_openai_api_key"
export TWILIO_ACCOUNT_SID="your_twilio_account_sid"
export TWILIO_AUTH_TOKEN="your_twilio_auth_token"
export PHONE_NUMBER_FROM="+15551234567"

# デプロイ実行
./deploy.sh
```

### 現在のデプロイ状況

- **サービス名**: speech-assistant-outbound
- **リージョン**: asia-northeast1
- **URL**: https://speech-assistant-outbound-hkzk5xnm7q-an.a.run.app
- **ステータス**: 運用中

### デプロイ後の管理

```bash
# サービス状況確認
gcloud run services describe speech-assistant-outbound --region=asia-northeast1

# ログ確認
gcloud run services logs read speech-assistant-outbound --region=asia-northeast1

# 再デプロイ
./deploy.sh
```

## 環境設定

### Cloud Run 用 (.env の現在設定)

```env
TWILIO_ACCOUNT_SID="ACcec80a2903fd4c3f7b287d8600565d27"
TWILIO_AUTH_TOKEN="ae91816925221569e1f9b63b8efcdc92"
PHONE_NUMBER_FROM="+15676011645"
DOMAIN='speech-assistant-outbound-hkzk5xnm7q-an.a.run.app'
OPENAI_API_KEY="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"
PORT=8080
```

### ローカル開発用 (.env 設定例)

```env
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
PHONE_NUMBER_FROM="+15551234567"
DOMAIN="abc123.ngrok.app"  # ngrok使用時
OPENAI_API_KEY="your_openai_api_key"
PORT=8080
```

### 3. 発信許可番号の設定

発信先の電話番号は以下のいずれかに登録されている必要があります：
- Twilio Verified Caller IDs
- Twilio所有の電話番号

## 実行方法

### Cloud Run デプロイ版の利用（推奨）

GCPにデプロイ済みのサーバーを利用する場合：

```bash
# ヘルスチェック
curl https://speech-assistant-outbound-hkzk5xnm7q-an.a.run.app/

# アウトバウンドコール実行
curl -X POST https://speech-assistant-outbound-hkzk5xnm7q-an.a.run.app/outbound-call \
  -H "Content-Type: application/json" \
  -d '{"to_number":"+81901234567"}'
```

### ローカル開発・動作確認

#### 1. ローカルサーバー起動（サーバーのみ）

```bash
# サーバーを起動
python main.py --server-only
```

ローカルサーバーが起動したら、別のターミナルでテスト：

```bash
# ヘルスチェック
curl http://localhost:8080/

# アウトバウンドコール実行（ローカル経由）
curl -X POST http://localhost:8080/outbound-call \
  -H "Content-Type: application/json" \
  -d '{"to_number":"+81901234567"}'
```

#### 2. 発信とサーバーを同時起動

```bash
# 発信を行いつつサーバーを起動
python main.py --call=+818079399927
```

#### 3. ngrok を使ったローカル公開（完全ローカル環境）

ngrokを使用してローカルサーバーを外部公開する場合：

```bash
# 1. ターミナル1: ngrok起動
ngrok http 8080

# 2. .envファイルのDOMAINを ngrok URL に変更
# 例：DOMAIN='abc123.ngrok.app'

# 3. ターミナル2: サーバー起動
python main.py --server-only

# 4. ターミナル3: テスト発信
curl -X POST http://localhost:8080/outbound-call \
  -H "Content-Type: application/json" \
  -d '{"to_number":"+81901234567", "user_id": "<userid:4CC0CA6A-657C-4253-99FF-C19219D30AE2>"}'
```

## システム構成

### Cloud Run デプロイ版

```
[発信者] ←→ [Twilio Voice] ←→ [Cloud Run Service] ←→ [OpenAI Realtime API]
                    ↑                ↑
                 WebSocket      HTTPS/WSS
```

### ローカル開発版

```
[発信者] ←→ [Twilio Voice] ←→ [ローカルサーバー + ngrok] ←→ [OpenAI Realtime API]
                    ↑                ↑
                 WebSocket      WebSocket + ngrok
```

### 共通フロー

1. **発信フロー**: Twilioが指定番号に発信
2. **音声接続**: TwilioがWebSocket経由でサーバーに接続
3. **AI処理**: サーバーがOpenAI Realtime APIと通信
4. **応答**: AIの音声応答が発信者に届く

## API エンドポイント

### GET /
ヘルスチェック用エンドポイント

**レスポンス:**
```json
{"message": "Twilio Outbound Call Server is running!"}
```

### POST /outbound-call
アウトバウンドコール実行用エンドポイント

**リクエスト:**
```json
{
  "to_number": "+81901234567",
  "message": "発信メッセージ（オプション）"
}
```

**レスポンス (成功時):**
```json
{
  "success": true,
  "call_sid": "CA1234567890abcdef",
  "to_number": "+81901234567",
  "message": "Call initiated successfully"
}
```

**レスポンス (エラー時):**
```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

### WebSocket /media-stream
Twilio音声ストリーミング用WebSocketエンドポイント（Twilio内部使用）

## トラブルシューティング

### よくあるエラー

#### 1. 環境変数未設定
```bash
❌ Error: OPENAI_API_KEY is not set
```
**解決方法**: `.env`ファイルが正しく設定されているか確認

#### 2. 発信許可エラー
```json
{"success": false, "error": "+81901234567 は発信許可がありません"}
```
**解決方法**: 発信先番号がTwilio Verified Caller IDsに登録されているか確認

#### 3. Cloud Run接続エラー
```bash
curl: (7) Failed to connect to speech-assistant-outbound-hkzk5xnm7q-an.a.run.app
```
**解決方法**: 
- Cloud Runサービスが起動しているか確認
- URLが正しいか確認

#### 4. ローカル ngrok接続エラー
```bash
WebSocket connection failed
```
**解決方法**: 
- ngrokが起動しているか確認
- `.env`のDOMAINが正しく設定されているか確認

#### 5. OpenAI API エラー
```json
{"error": "Invalid API key"}
```
**解決方法**: 
- APIキーが有効か確認
- Realtime API利用権限があるか確認

### ログの確認

#### Cloud Run ログ
```bash
gcloud run services logs read speech-assistant-outbound --region=asia-northeast1 --limit=50
```

#### ローカル ログ
詳細なログを確認したい場合は、`logging.basicConfig`のレベルを`DEBUG`に設定してください（デフォルトで有効）。

### 動作確認用テストコマンド

```bash
# 1. ヘルスチェック（Cloud Run）
curl https://speech-assistant-outbound-hkzk5xnm7q-an.a.run.app/

# 2. ヘルスチェック（ローカル）
curl http://localhost:8080/

# 3. 発信テスト（実際に電話をかけるので注意）
curl -X POST https://speech-assistant-outbound-hkzk5xnm7q-an.a.run.app/outbound-call \
  -H "Content-Type: application/json" \
  -d '{"to_number":"+81901234567"}' \
  -v
```

## 注意事項

### 重要な制限事項
- **電話番号制限**: Twilio試用版では検証済み番号のみに発信可能
- **API使用料金**: TwilioとOpenAI APIの使用料金が発生します
- **セキュリティ**: 本番環境では適切な認証・認可の実装が必要

### プロダクション運用時の考慮事項
- 環境変数の安全な管理（Secret Manager等の使用）
- ログレベルの調整（本番ではINFO以上推奨）
- エラーハンドリングの強化
- レート制限の実装
- 監視・アラート設定

## 主な機能
- ✅ OpenAI Realtime API を使った音声対話
- ✅ Twilio Voice による電話発信
- ✅ リアルタイム音声ストリーミング
- ✅ 日本語での自然な会話
- ✅ Cloud Run での本番運用対応
- ✅ ローカル開発環境サポート
