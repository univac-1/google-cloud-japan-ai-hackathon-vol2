"""
サブコレクション構造対応API テストスクリプト
users/{userID}/calls/{callID} 形式のAPIテスト
"""
import requests
import json

def test_subcollection_api():
    """
    サブコレクション構造対応APIの包括的テスト
    """
    base_url = "http://localhost:8080"
    
    print("=== サブコレクション構造対応API テスト開始 ===")
    
    # テストデータ
    test_user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    test_call_id = "CA995a950a2b9f6623a5adc987d0b31131"
    
    test_cases = [
        {
            "name": "正常ケース1: 指定された会話履歴取得",
            "endpoint": "/get-conversation-history-v2",
            "payload": {"userID": test_user_id, "callID": test_call_id},
            "expected_status": 200,
            "description": "指定されたuserIDとcallIDで会話履歴を正常取得"
        },
        {
            "name": "正常ケース2: 別の会話履歴取得",
            "endpoint": "/get-conversation-history-v2",
            "payload": {"userID": test_user_id, "callID": "CALL002"},
            "expected_status": 200,
            "description": "同じユーザーの別の会話履歴を正常取得"
        },
        {
            "name": "正常ケース3: ユーザーの全会話履歴取得",
            "endpoint": "/get-user-calls",
            "payload": {"userID": test_user_id},
            "expected_status": 200,
            "description": "指定ユーザーのすべての会話履歴を取得"
        },
        {
            "name": "エラーケース1: 存在しないユーザー",
            "endpoint": "/get-conversation-history-v2",
            "payload": {"userID": "NONEXISTENT", "callID": test_call_id},
            "expected_status": 404,
            "description": "存在しないユーザーIDでエラー確認"
        },
        {
            "name": "エラーケース2: 存在しない会話ID",
            "endpoint": "/get-conversation-history-v2",
            "payload": {"userID": test_user_id, "callID": "NONEXISTENT"},
            "expected_status": 404,
            "description": "存在しない会話IDでエラー確認"
        },
        {
            "name": "エラーケース3: userID不正",
            "endpoint": "/get-conversation-history-v2",
            "payload": {"callID": test_call_id},
            "expected_status": 400,
            "description": "userID未指定でバリデーションエラー確認"
        }
    ]
    
    # ヘルスチェック
    print("\n--- ヘルスチェック ---")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ サービスが起動しています")
        else:
            print(f"❌ サービス起動確認失敗: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ サービスに接続できません。サービスが起動していることを確認してください。")
        return
    
    # テストケース実行
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- テスト {i}/{total_count}: {test_case['name']} ---")
        print(f"説明: {test_case['description']}")
        print(f"エンドポイント: {test_case['endpoint']}")
        print(f"ペイロード: {json.dumps(test_case['payload'], ensure_ascii=False)}")
        print(f"期待ステータス: {test_case['expected_status']}")
        
        try:
            response = requests.post(
                f"{base_url}{test_case['endpoint']}",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"実際ステータス: {response.status_code}")
            
            if response.status_code == test_case['expected_status']:
                print("✅ ステータスコードが期待値と一致")
                success_count += 1
                
                # 成功レスポンスの内容確認
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get("status") == "success":
                        print("✅ レスポンス形式が正常")
                        
                        # 詳細情報表示
                        data = response_data.get("data", {})
                        if test_case['endpoint'] == "/get-conversation-history-v2":
                            user_info = data.get("user_info", {})
                            conv_history = data.get("conversation_history", {})
                            print(f"   ユーザー: {user_info.get('name')}")
                            print(f"   会話ID: {conv_history.get('callID')}")
                            print(f"   会話数: {len(conv_history.get('conversation', []))}")
                            print(f"   Firestoreパス: {data.get('firestore_path')}")
                        elif test_case['endpoint'] == "/get-user-calls":
                            user_info = data.get("user_info", {})
                            calls_count = data.get("calls_count", 0)
                            print(f"   ユーザー: {user_info.get('name')}")
                            print(f"   会話履歴数: {calls_count}")
                            if calls_count > 0:
                                calls = data.get("calls", [])
                                for call in calls:
                                    print(f"     - {call.get('callID')}: {call.get('status')}")
                    else:
                        print("❌ レスポンス形式が異常")
                else:
                    # エラーレスポンスの確認
                    response_data = response.json()
                    print(f"   エラーコード: {response_data.get('error_code')}")
                    print(f"   エラーメッセージ: {response_data.get('message')}")
            else:
                print(f"❌ ステータスコードが期待値と不一致")
                print(f"レスポンス: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ リクエストエラー: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSONパースエラー: {str(e)}")
            print(f"レスポンステキスト: {response.text}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {str(e)}")
    
    # テスト結果サマリー
    print(f"\n=== テスト結果サマリー ===")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("✅ すべてのテストが成功しました！")
    else:
        print(f"❌ {total_count - success_count}件のテストが失敗しました。")

def test_specific_call():
    """
    特定の会話履歴の詳細テスト
    """
    base_url = "http://localhost:8080"
    user_id = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
    call_id = "CA995a950a2b9f6623a5adc987d0b31131"
    
    print(f"\n=== 特定会話履歴詳細テスト ===")
    print(f"UserID: {user_id}")
    print(f"CallID: {call_id}")
    
    try:
        response = requests.post(
            f"{base_url}/get-conversation-history-v2",
            json={"userID": user_id, "callID": call_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 会話履歴取得成功")
            
            # 詳細データを整理して表示
            conversation_data = data['data']['conversation_history']
            print(f"\n📞 会話詳細:")
            print(f"   CallID: {conversation_data['callID']}")
            print(f"   タイプ: {conversation_data['call_type']}")
            print(f"   ステータス: {conversation_data['status']}")
            print(f"   時間: {conversation_data['duration_seconds']}秒")
            
            conversations = conversation_data['conversation']
            print(f"\n💬 会話内容 ({len(conversations)}件):")
            for i, conv in enumerate(conversations, 1):
                speaker = conv['speaker']
                message = conv['message']
                print(f"   {i}. {speaker}: {message[:100]}...")
            
            ai_analysis = conversation_data.get('ai_analysis', {})
            if ai_analysis:
                print(f"\n🤖 AI分析:")
                print(f"   健康状態: {ai_analysis.get('health_status')}")
                print(f"   懸念事項: {ai_analysis.get('concerns')}")
                print(f"   推奨事項: {ai_analysis.get('recommendations')}")
                print(f"   緊急度: {ai_analysis.get('urgency_level')}")
        else:
            print(f"❌ 取得失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")

if __name__ == "__main__":
    print("サブコレクション構造対応APIテストを開始します...")
    
    # 基本的なAPIテスト
    test_subcollection_api()
    
    # 特定の会話履歴の詳細テスト
    test_specific_call()
    
    print("\nサブコレクション構造対応APIテストが完了しました。") 