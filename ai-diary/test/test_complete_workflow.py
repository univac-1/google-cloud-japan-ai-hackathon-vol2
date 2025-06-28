#!/usr/bin/env python3
"""
完全な一連の処理の動作確認スクリプト
ユーザー情報取得→会話履歴取得→日記生成→挿絵作成
"""

import requests
import json
import sys
import time

def test_complete_flow():
    """
    完全な一連の処理をテストする
    """
    base_url = "http://localhost:8080"
    
    # テストデータ - 実際のデータが存在するユーザーIDとcallIDを使用
    test_cases = [
        {
            "userID": "user_001",
            "callID": "call_20231201_001",
            "description": "テストユーザー001の12月1日の通話"
        },
        {
            "userID": "test-user-123", 
            "callID": "test-call-456",
            "description": "テスト用ダミーデータ"
        }
    ]
    
    print("=== 完全な一連処理テスト開始 ===")
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n--- テストケース {i}: {test_data['description']} ---")
        print(f"UserID: {test_data['userID']}")
        print(f"CallID: {test_data['callID']}")
        
        try:
            # API呼び出し
            url = f"{base_url}/generate-diary"
            request_data = {
                "userID": test_data["userID"],
                "callID": test_data["callID"]
            }
            
            print(f"\n📤 リクエスト送信中...")
            start_time = time.time()
            
            response = requests.post(url, json=request_data, timeout=120)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"⏱️ 処理時間: {elapsed_time:.2f}秒")
            print(f"📊 ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    result_data = data.get('data', {})
                    
                    print("✅ 一連の処理が成功しました！")
                    print(f"📝 日記長さ: {len(result_data.get('diary', ''))}文字")
                    
                    # 日記の一部を表示
                    diary_text = result_data.get('diary', '')
                    if diary_text:
                        preview = diary_text[:100] + "..." if len(diary_text) > 100 else diary_text
                        print(f"📖 日記プレビュー: {preview}")
                    
                    # 挿絵URLの確認
                    illustration_url = result_data.get('illustrationUrl')
                    if illustration_url:
                        print(f"🎨 挿絵URL: {illustration_url}")
                    else:
                        print("⚠️ 挿絵の生成に失敗しました（エラーは継続処理済み）")
                    
                    # ユーザー情報の確認
                    user_info = result_data.get('userInfo', {})
                    if user_info:
                        print(f"👤 ユーザー名: {user_info.get('name', '不明')}")
                        print(f"🎂 年齢: {user_info.get('age', '不明')}")
                        print(f"⚧ 性別: {user_info.get('gender', '不明')}")
                    
                    # 会話履歴の確認
                    conversation = result_data.get('conversationHistory', {})
                    if conversation:
                        messages = conversation.get('messages', [])
                        print(f"💬 会話メッセージ数: {len(messages)}")
                    
                    return True
                else:
                    print(f"❌ APIエラー: {data.get('message', '不明なエラー')}")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ HTTPエラー {response.status_code}: {error_data.get('message', '不明なエラー')}")
                except:
                    print(f"❌ HTTPエラー {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ リクエストがタイムアウトしました（120秒）")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ サーバーに接続できませんでした")
            return False
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            return False
    
    return False

def check_server():
    """
    サーバーが起動しているか確認
    """
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("=== AI Diary Service 一連処理動作確認 ===")
    
    # サーバー起動確認
    if not check_server():
        print("❌ サーバーが起動していません。")
        print("先にサーバーを起動してください:")
        print("  cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary")
        print("  python3 main.py")
        sys.exit(1)
    
    print("✅ サーバーが起動しています")
    
    # 完全な処理テスト実行
    success = test_complete_flow()
    
    print(f"\n=== テスト完了 ===")
    if success:
        print("✅ 一連の処理が正常に動作しています！")
        sys.exit(0)
    else:
        print("❌ 一連の処理にエラーがありました")
        sys.exit(1)
