# テストファイル

このディレクトリには、AI日記アプリケーションの必要最小限のテスト関連ファイルが格納されています。

## 必要最小限のテストファイル

- `quick_test.py` - 基本的なAPIテスト（ヘルスチェック、主要エンドポイント）
- `test_db_connection.py` - データベース接続テスト
- `check_environment.py` - 環境変数と接続確認

## 使用方法

```bash
# 環境変数確認
python test/check_environment.py

# DB接続テスト
python test/test_db_connection.py

# 基本的なAPIテスト
python test/quick_test.py
```
- `test_diary_api.sh` - 日記API テストスクリプト
- `test_complete_api.sh` - 完全API テストスクリプト
- `test_complete_api_with_html.sh` - HTML付き完全API テストスクリプト
- `test_html_api.sh` - HTML API テストスクリプト
- `test_email_api.sh` - メール API テストスクリプト
- `test_specified_params.sh` - 指定パラメータテストスクリプト

## テスト実行方法

```bash
# 全テスト実行
cd test
./run_full_test.sh

# 個別テスト実行例
python test_integration.py
python gemini_test.py
```
