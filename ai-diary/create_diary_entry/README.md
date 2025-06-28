# AI Diary Entry Generator

Gemini APIを使用してユーザー情報と会話履歴から家族向けの日記風文章を生成する機能です。

## 概要

高齢者の安否確認アプリの会話データを元に、家族が読んで安心できる温かみのある日記風の文章を自動生成します。

## 機能

- **日記生成**: ユーザー情報と会話履歴から日記風の文章を生成
- **家族向け**: 家族が読んで安心できる内容に調整
- **温かみのある文体**: 敬語を使わず親しみやすい表現
- **プライバシー配慮**: センシティブな情報を適切に処理

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install google-genai
```

### 2. Gemini API キーの取得と設定

1. [Google AI Studio](https://ai.google.dev/) にアクセス
2. APIキーを取得
3. 環境変数に設定:

```bash
export GEMINI_API_KEY=your_api_key_here
```

または、`.env`ファイルに追記:

```
GEMINI_API_KEY=your_api_key_here
```

### 3. 動作確認

```bash
cd ai-diary
./test_gemini_api.sh
```

## 使用方法

### 基本的な使用例

```python
from create_diary_entry import DiaryGenerator

# インスタンス作成
generator = DiaryGenerator()

# ユーザー情報
user_info = {
    "name": "山田太郎",
    "last_name": "山田",
    "first_name": "太郎",
    "birth_date": "1949-05-15",
    "prefecture": "東京都",
    "address_block": "渋谷区"
}

# 会話履歴
conversation_history = {
    "conversation": [
        {"role": "assistant", "text": "おはようございます、山田さん。"},
        {"role": "user", "text": "おはよう。今日は孫が来るんだ。"},
        {"role": "assistant", "text": "それは楽しみですね。"},
        {"role": "user", "text": "一緒に公園に行く予定だよ。"}
    ]
}

# 日記生成
success, diary, error = generator.generate_diary_entry(user_info, conversation_history)

if success:
    print("生成された日記:")
    print(diary)
else:
    print(f"エラー: {error}")
```

### API統合例

```python
from create_diary_entry import DiaryGenerator
from flask import Flask, request, jsonify

app = Flask(__name__)
generator = DiaryGenerator()

@app.route('/generate-diary', methods=['POST'])
def generate_diary():
    """日記生成APIエンドポイント"""
    try:
        data = request.get_json()
        user_info = data.get('userInfo', {})
        conversation_history = data.get('conversationHistory', {})
        
        success, diary, error = generator.generate_diary_entry(
            user_info, conversation_history
        )
        
        if success:
            return jsonify({
                "status": "success",
                "diary": diary
            })
        else:
            return jsonify({
                "status": "error",
                "message": error
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

## 出力形式

生成される日記は以下の形式になります:

```
2024年12月01日 山田太郎さんの一日

今日の山田太郎さんはとても嬉しそうでした。孫が遊びに来ることを楽しみにしていて、一緒に近所の公園へお散歩に行く予定を立てています。お天気も良く、きっと素敵な時間を過ごせそうです。久しぶりに孫と会えることを心から楽しみにしている様子が伝わってきました。
```

## クラス構成

### DiaryGenerator

メインの日記生成クラス

**メソッド:**

- `generate_diary_entry(user_info, conversation_history)`: 日記生成
- `test_generation()`: 動作テスト

**引数:**

- `user_info`: ユーザー情報辞書
- `conversation_history`: 会話履歴辞書

**戻り値:**

- `Tuple[bool, Optional[str], Optional[str]]`: (成功フラグ, 日記文章, エラーメッセージ)

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `GEMINI_API_KEY` | Gemini API キー | ✅ |

## エラーハンドリング

- APIキー未設定: `ValueError`
- ライブラリ未インストール: `ImportError`
- API呼び出し失敗: 詳細なエラーメッセージを返却

## テスト

```bash
# 基本テスト
cd create_diary_entry
python gemini_test.py

# 統合テスト
cd ai-diary
./test_gemini_api.sh
```

## 制限事項

- Gemini APIの利用制限に依存
- インターネット接続が必要
- 日本語での生成に最適化

## トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - `GEMINI_API_KEY`環境変数が正しく設定されているか確認

2. **ライブラリエラー**
   - `pip install google-genai`が実行されているか確認

3. **生成エラー**
   - 入力データの形式が正しいか確認
   - APIの利用制限に達していないか確認

### ログ確認

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## ライセンス

MIT License 