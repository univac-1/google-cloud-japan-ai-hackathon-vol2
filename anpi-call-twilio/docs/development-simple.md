# 開発者ガイド

## 開発環境セットアップ

### 1. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数設定
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### 3. ローカル実行
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## 開発フロー

### 1. コード変更
- `main.py` でアプリケーションロジック修正
- `requirements.txt` で依存関係管理

### 2. ローカルテスト
```bash
# サーバー起動
uvicorn main:app --reload

# ヘルスチェック
curl http://localhost:8080/
```

### 3. デプロイ
```bash
export OPENAI_API_KEY="your_key"
./deploy.sh
```

## コードストラクチャ

### main.py の主要コンポーネント

- **`/`**: ヘルスチェックエンドポイント
- **`/incoming-call`**: Twilio Webhook処理
- **`/media-stream`**: WebSocket音声ストリーム処理
- **`RealtimeClient`**: OpenAI Realtime API接続クラス

### 重要な設定

```python
# WebSocket設定
OPENAI_WS_URL = "wss://api.openai.com/v1/realtime"

# Audio設定
SAMPLE_RATE = 24000
AUDIO_FORMAT = "pcm16"
```

## デバッグ

### ローカルログ
```bash
# 詳細ログ有効化
export LOG_LEVEL=DEBUG
uvicorn main:app --log-level debug
```

### Cloud Runログ
```bash
gcloud run services logs read speech-assistant-openai --region=asia-northeast1 --follow
```

## 注意事項

1. **OpenAI API制限**: レート制限に注意
2. **WebSocket接続**: 適切な切断処理実装済み
3. **Twilio署名**: セキュリティ検証実装済み
