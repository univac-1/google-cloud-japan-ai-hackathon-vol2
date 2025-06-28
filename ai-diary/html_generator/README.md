# HTML Generator パッケージ

## 概要

日記テキストを外部APIを使用してHTMLページに変換するパッケージです。

## 機能

- 日記テキストからHTMLページの生成
- HTML生成APIとの連携
- エラーハンドリング
- APIテスト機能

## 使用方法

### 基本的な使用例

```python
from html_generator.generator import generate_html_page

# HTMLページ生成（テスト用固定パラメータ）
html_content = generate_html_page(
    text_content="今日は良い天気でした。",
    user_id="4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    call_id="CA995a950a2b9f6623a5adc987d0b31131"
)

if html_content:
    print("HTML生成成功:", html_content)
else:
    print("HTML生成失敗")
```

### APIテスト

```python
from html_generator.generator import test_html_generation

# HTML生成APIのテスト
if test_html_generation():
    print("HTML生成API正常")
else:
    print("HTML生成API異常")
```

## API仕様

### HTML生成API
- **URL**: `https://eniki-html-generator-hkzk5xnm7q-an.a.run.app/process-text`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `text_content`: 日記テキスト
  - `user_id`: ユーザーID
  - `call_id`: 通話ID

## エラーハンドリング

- APIタイムアウト（30秒）
- HTTPエラーレスポンス
- ネットワークエラー
- 予期しない例外

## テストユーザー情報

動作確認には以下の固定パラメータを使用：

- **userID**: `4CC0CA6A-657C-4253-99FF-C19219D30AE2`
- **callID**: `CA995a950a2b9f6623a5adc987d0b31131`
