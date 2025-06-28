#!/bin/bash

# Gemini API 動作確認テストスクリプト
# 日記生成機能のテストを実行します

set -e

echo "=== Gemini API 動作確認テスト ==="

# 基本設定の読み込み
if [[ -f "config.env" ]]; then
    echo "config.envを読み込み中..."
    source config.env
else
    echo "config.envファイルが見つかりません"
    exit 1
fi

# 仮想環境をアクティブ化
if [[ -f "venv/bin/activate" ]]; then
    echo "仮想環境をアクティブ化中..."
    source venv/bin/activate
else
    echo "仮想環境が見つかりません。まず以下を実行してください:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# GEMINI_API_KEYの確認
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ GEMINI_API_KEY環境変数が設定されていません"
    echo ""
    echo "以下の手順でAPIキーを設定してください:"
    echo "1. https://ai.google.dev/ にアクセス"
    echo "2. Google AI Studio でAPIキーを取得"
    echo "3. export GEMINI_API_KEY=your_api_key_here"
    echo ""
    echo "または、config.envファイルに以下を追記:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo "その後、source config.env を実行"
    exit 1
fi

echo "✅ GEMINI_API_KEY設定確認済み"

# 必要なライブラリのインストール確認
echo "必要なライブラリをインストール中..."
pip install -q google-genai

# テストスクリプト実行
echo ""
echo "=== Gemini API 動作テスト実行 ==="
cd create_diary_entry
python gemini_test.py

echo ""
echo "=== DiaryGenerator クラステスト ==="
python -c "
from gemini_service import DiaryGenerator
import sys

try:
    print('📝 DiaryGenerator クラステスト開始...')
    generator = DiaryGenerator()
    
    if generator.test_generation():
        print('✅ DiaryGenerator テスト成功')
        sys.exit(0)
    else:
        print('❌ DiaryGenerator テスト失敗')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ DiaryGenerator テストエラー: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 すべてのテストが完了しました！"
echo "✅ Gemini API動作確認成功"
echo "📝 日記生成機能の実装が完了しました" 