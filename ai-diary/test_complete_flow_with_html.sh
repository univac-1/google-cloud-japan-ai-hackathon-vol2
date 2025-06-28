#!/bin/bash

# HTML生成を含む完全な日記生成フローのテスト（Python版）

echo "=== HTML生成を含む完全な日記生成フローのテスト（Python版） ==="

# 仮想環境をアクティベート
source venv/bin/activate

# 環境変数の読み込み（.envファイルから）
source .env

# Pythonテストスクリプトを実行
python test_complete_flow_with_html.py

echo ""
echo "=== テスト完了 ==="
