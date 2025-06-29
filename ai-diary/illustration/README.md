# Illustration Generator

日記内容に基づいてイラストを生成する処理モジュール

## 機能

- 日記内容からプロンプトを生成
- Vertex AI Imagen APIでイラスト生成
- 生成画像のCloud Storage保存

## ファイル構成

- `generator.py` - イラスト生成処理
- `prompt_builder.py` - プロンプト構築処理

## 使用方法

```python
from illustration.generator import generate_illustration

illustration_url = generate_illustration(diary_text, user_id, gender, call_id)
```
