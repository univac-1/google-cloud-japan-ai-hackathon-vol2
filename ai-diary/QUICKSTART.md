# AI Diary Service - クイックスタートガイド

## 最初の動作確認（5分で確認）

### 1. 環境準備
```bash
# プロジェクトディレクトリに移動
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary

# 仮想環境をアクティベート
source ai_diary_env/bin/activate

# Gemini APIキーを設定
export GEMINI_API_KEY="AIzaSyBINVVUZhQVP3IS1ht1RBxguS9ajibSq-c"
```

### 2. 基本動作確認
```bash
# Gemini API接続テスト
python test_gemini_simple.py

# サンプルデータでの日記生成テスト
python test_sample_data.py
```

### 3. 期待される結果
成功時には以下のような日記が生成されます：

```
✅ 日記生成テスト成功!

📄 生成された日記:
============================================================
タイトル: 2025年06月28日 田中さんの一日

今日は朝から調子がいいんだ！久しぶりに体が軽くて、なんだか嬉しい一日になりそう。
朝ごはんもいつもよりたくさん食べられたしね。午前中はゆっくりとラジオ体操をして、
庭の草花に水をあげたよ。

午後には、娘と孫娘が遊びに来てくれる予定なんだ！7歳になる元気いっぱいの女の子でね、
一緒に絵を描く約束をしているんだ。孫娘が来るってだけで、家の中が明るくなった気がする。
久しぶりに賑やかな時間になるのが、本当に楽しみ！
============================================================
```

## 推奨テストパラメータ

すべてのテストで以下のパラメータを使用します：

- **userID**: `4CC0CA6A-657C-4253-99FF-C19219D30AE2`
- **callID**: `CA995a950a2b9f6623a5adc987d0b31131`

## トラブルシューティング

### よくあるエラーと対処法

1. **GEMINI_API_KEY環境変数が設定されていません**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

2. **ModuleNotFoundError: No module named 'google.generativeai'**
   ```bash
   pip install google-generativeai
   ```

3. **DB接続エラー（Can't connect to MySQL server）**
   - Cloud SQL Proxyが起動していない場合は、DB不要のテストから始めてください
   - `python test_sample_data.py` を実行

4. **ImportError: cannot import name 'firestore'**
   ```bash
   pip install google-cloud-firestore
   ```

## 次のステップ

基本動作が確認できたら：

1. **DB接続テスト**: `python test_integration.py`
2. **Flaskサーバー起動**: `python main.py`
3. **API経由テスト**: `curl` または Postman で `/generate-diary` エンドポイントをテスト

詳細は `README.md` をご覧ください。
