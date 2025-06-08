# プロジェクト概要

## アーキテクチャ

```
[電話] → [Twilio] → [Cloud Run] → [OpenAI Realtime API]
                        ↓
                   [WebSocket通信]
```

### 技術スタック
- **Runtime**: Python 3.11 + FastAPI
- **Infrastructure**: Google Cloud Run
- **External APIs**: OpenAI Realtime API, Twilio
- **Communication**: WebSocket + HTTP

### エンドポイント
- **Root**: `/` - ヘルスチェック
- **Incoming Call**: `/incoming-call` - Twilio Webhook
- **Media Stream**: `/media-stream` - WebSocket接続

## プロジェクト構成

```
├── main.py              # メインアプリケーション
├── requirements.txt     # Python依存関係
├── Dockerfile          # コンテナ設定
├── cloudbuild.yaml     # CI/CD設定
├── deploy.sh           # デプロイスクリプト
└── docs/               # ドキュメント
```

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API キー | ✅ |
| `PORT` | サーバーポート | ❌ (デフォルト: 8080) |

## サービス情報

- **プロジェクトID**: `univac-aiagent`
- **サービス名**: `speech-assistant-openai`
- **リージョン**: `asia-northeast1`
- **URL**: `https://speech-assistant-openai-hkzk5xnm7q-an.a.run.app`
