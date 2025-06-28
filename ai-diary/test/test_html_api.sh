#!/bin/bash

# HTML生成API単体テスト

echo "=== HTML生成API単体テスト ==="
echo "使用パラメータ: userID=4CC0CA6A-657C-4253-99FF-C19219D30AE2, callID=CA995a950a2b9f6623a5adc987d0b31131"
echo ""

# 仮想環境をアクティベート
source venv/bin/activate

# HTML生成テスト実行
echo "1. Python直接実行によるHTML生成テスト"
python html_generator/generator.py
echo ""

echo "2. 外部APIの直接テスト（curlコマンド）"
curl -X POST -H "Content-Type: multipart/form-data" \
  -F "text_content=これは
テスト画像付きの
テキストです。" \
  -F "user_id=4CC0CA6A-657C-4253-99FF-C19219D30AE2" \
  -F "call_id=CA995a950a2b9f6623a5adc987d0b31131" \
  https://eniki-html-generator-hkzk5xnm7q-an.a.run.app/process-text

echo ""
echo "=== HTML生成API単体テスト完了 ==="
