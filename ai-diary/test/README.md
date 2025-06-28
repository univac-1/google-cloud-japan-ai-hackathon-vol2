# テストファイル

このディレクトリには、AI日記アプリケーションのテスト関連ファイルが格納されています。

## テストファイル一覧

### 統合テスト
- `comprehensive_test.py` - 包括的なテスト
- `test_integration.py` - 統合テスト
- `quick_test.py` - クイックテスト

### API/サービステスト
- `test_api.py` - API テスト
- `test_subcollection_api.py` - サブコレクション API テスト
- `test_service.py` - サービステスト

### Gemini関連テスト
- `gemini_test.py` - Gemini サービステスト
- `test_gemini_local.py` - ローカル Gemini テスト
- `test_gemini_simple.py` - シンプル Gemini テスト

### データテスト
- `test_real_data.py` - 実データテスト
- `test_sample_data.py` - サンプルデータテスト
- `create_realistic_test_data.py` - リアルなテストデータ作成
- `create_subcollection_test_data.py` - サブコレクションテストデータ作成
- `create_test_data.py` - テストデータ作成

### アプリケーションテスト
- `test_diary_standalone.py` - 日記スタンドアロンテスト
- `test_local_flask.py` - ローカル Flask テスト
- `test_summary.py` - サマリーテスト

### シェルスクリプト
- `test_gemini_api.sh` - Gemini API テストスクリプト
- `test_service.sh` - サービステストスクリプト
- `run_full_test.sh` - 全テスト実行スクリプト

## テスト実行方法

```bash
# 全テスト実行
cd test
./run_full_test.sh

# 個別テスト実行例
python test_integration.py
python gemini_test.py
```
