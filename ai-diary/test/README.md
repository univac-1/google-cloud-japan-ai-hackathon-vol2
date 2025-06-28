# テストファイル

このディレクトリには、AI日記アプリケーションのテスト関連ファイルが格納されています。

## テストファイル一覧

### 統合テスト
- `comprehensive_test.py` - 包括的なテスト
- `test_integration.py` - 統合テスト
- `test_complete_workflow.py` - 完全なワークフローテスト
- `quick_test.py` - クイックテスト

### API/サービステスト
- `test_api.py` - API テスト
- `test_subcollection_api.py` - サブコレクション API テスト
- `test_service.py` - サービステスト
- `test_diary_standalone.py` - 日記スタンドアロンテスト

### Gemini関連テスト
- `gemini_test.py` - Gemini サービステスト

### データテスト・管理
- `test_real_data.py` - 実データテスト
- `test_sample_data.py` - サンプルデータテスト
- `test_specified_params_sample.py` - 指定パラメータサンプルテスト
- `create_realistic_test_data.py` - リアルなテストデータ作成
- `create_subcollection_test_data.py` - サブコレクションテストデータ作成
- `create_test_data.py` - テストデータ作成
- `check_test_data.py` - テストデータ確認
- `check_existing_data.py` - 既存データ確認
- `examine_data.py` - データ検査

### 環境・接続テスト
- `check_environment.py` - 環境変数と接続テスト
- `test_db_connection.py` - データベース接続テスト
- `debug_db_connection.py` - データベース接続デバッグ

### Firestore関連
- `firestore_info.py` - Firestore情報取得
- `search_all_collections.py` - 全コレクション検索
- `check_subcollection_structure.py` - サブコレクション構造確認

### その他
- `test_summary.py` - サマリーテスト
- `test_complete_flow_with_html.py` - HTML付き完全フローテスト

### シェルスクリプト
- `run_full_test.sh` - 全テスト実行スクリプト
- `test_gemini_api.sh` - Gemini API テストスクリプト
- `test_service.sh` - サービステストスクリプト
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
