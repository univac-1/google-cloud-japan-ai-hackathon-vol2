"""
HTML生成サービス
日記テキストを外部APIでHTMLページに変換する
"""

import requests
import os
from typing import Optional, Tuple


def generate_html_page(text_content: str, user_id: str, call_id: str) -> Optional[str]:
    """
    日記テキストからHTMLページを生成する
    
    Args:
        text_content (str): 日記の本文
        user_id (str): ユーザーID
        call_id (str): 通話ID
        
    Returns:
        Optional[str]: 生成されたHTMLコンテンツ（エラー時はNone）
    """
    try:
        # HTML生成APIのエンドポイント
        api_url = "https://eniki-html-generator-hkzk5xnm7q-an.a.run.app/process-text"
        
        # APIリクエストのデータ準備
        files = {
            'text_content': (None, text_content),
            'user_id': (None, user_id),
            'call_id': (None, call_id)
        }
        
        # APIリクエスト送信
        response = requests.post(api_url, files=files, timeout=30)
        
        # レスポンスチェック
        if response.status_code == 200:
            return response.text
        else:
            print(f"HTML生成API エラー: ステータス {response.status_code}")
            print(f"レスポンス: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("HTML生成API タイムアウトエラー")
        return None
    except requests.exceptions.RequestException as e:
        print(f"HTML生成API リクエストエラー: {str(e)}")
        return None
    except Exception as e:
        print(f"HTML生成処理中の予期しないエラー: {str(e)}")
        return None


def test_html_generation() -> bool:
    """
    HTML生成APIの動作テスト
    
    Returns:
        bool: テスト成功時True
    """
    try:
        test_text = "これは\nテスト画像付きの\nテキストです。"
        # READMEで指定された固定のテスト用パラメータを使用
        test_user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
        test_call_id = "CA995a950a2b9f6623a5adc987d0b31131"
        
        print(f"テスト用パラメータ:")
        print(f"  ユーザーID: {test_user_id}")
        print(f"  コールID: {test_call_id}")
        print(f"  テキスト: {test_text}")
        print()
        
        html_content = generate_html_page(test_text, test_user_id, test_call_id)
        
        if html_content:
            print("✅ HTML生成APIテスト成功")
            print(f"HTMLコンテンツ長: {len(html_content)} 文字")
            # HTMLの最初の100文字を表示
            preview = html_content[:100] if len(html_content) > 100 else html_content
            print(f"HTMLプレビュー: {preview}...")
            return True
        else:
            print("❌ HTML生成APIテスト失敗")
            return False
            
    except Exception as e:
        print(f"❌ HTML生成APIテストエラー: {str(e)}")
        return False


if __name__ == "__main__":
    # テスト実行
    test_html_generation()
