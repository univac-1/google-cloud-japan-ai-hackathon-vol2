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

### 2. 環境変数の設定

`.env`ファイルを編集して、実際の値を設定してください：

```env
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
PHONE_NUMBER_FROM="+15551234567"  # Twilio電話番号（E.164形式）
DOMAIN="your_ngrok_domain"        # ngrokドメイン
OPENAI_API_KEY="your_openai_api_key"
PORT=6060
```

### 3. ngrokの起動

別のターミナルでngrokを起動し、外部からアクセス可能にします：

```bash
ngrok http 6060
```

表示されたHTTPS URLのドメイン部分（例：`abc123.ngrok.app`）を`.env`の`DOMAIN`に設定してください。

### 4. 発信許可番号の設定

発信先の電話番号は以下のいずれかに登録されている必要があります：
- Twilio Verified Caller IDs
- Twilio所有の電話番号

## 実行方法

### サーバーのみ起動（推奨）

```bash
# サーバーを起動
python main.py --server-only
```

### 発信とサーバーを同時起動

```bash
# 発信を行いつつサーバーを起動
python main.py --call=+81901234567
```

### 使用例

1. **サーバーを起動**
   ```bash
   python main.py --server-only
   ```

2. **別のターミナルで発信テスト**
   ```bash
   # 検証済み番号への発信
   python -c "
   import asyncio
   from main import make_call
   asyncio.run(make_call('+81901234567'))
   "
   ```

## システム構成

```
[発信者] ←→ [Twilio Voice] ←→ [FastAPI Server] ←→ [OpenAI Realtime API]
                    ↑                ↑
                 WebSocket      WebSocket + ngrok
```

1. **発信フロー**: Twilioが指定番号に発信
2. **音声接続**: TwilioがWebSocket経由でサーバーに接続
3. **AI処理**: サーバーがOpenAI Realtime APIと通信
4. **応答**: AIの音声応答が発信者に届く

## トラブルシューティング

### よくあるエラー

1. **環境変数未設定**
   - `.env`ファイルが正しく設定されているか確認

2. **発信許可エラー**
   - 発信先番号がTwilio Verified Caller IDsに登録されているか確認

3. **ngrok接続エラー**
   - ngrokが起動しているか確認
   - `.env`のDOMAINが正しく設定されているか確認

4. **OpenAI API エラー**
   - APIキーが有効か確認
   - Realtime API利用権限があるか確認

### ログの確認

詳細なログを確認したい場合は、`logging.basicConfig`のレベルを`DEBUG`に設定してください（デフォルトで有効）。

## 注意事項

- 本システムはローカル開発・テスト用です
- プロダクション環境では適切なセキュリティ設定が必要です
- Twilioの使用料金と制限にご注意ください
- OpenAI Realtime APIの使用料金と制限にご注意ください
2. **Number not allowed**: Twilio Dev PhoneまたはVerified Caller IDsに発信先番号を登録
3. **ngrok connection failed**: ngrokが起動しているか、DOMAINが正しく設定されているか確認

### ログの確認
アプリケーションは詳細なログを出力します。エラーの詳細はターミナルで確認できます。

## 機能
- OpenAI Realtime API を使った音声対話
- Twilio Voice による電話発信
- リアルタイム音声ストリーミング
- 日本語での自然な会話
