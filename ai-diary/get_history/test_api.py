"""
会話履歴取得API テストスクリプト
"""
import requests
import json
import time

class ConversationHistoryAPITester:
    """会話履歴取得APIのテストクラス"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        
    def test_get_conversation_history(self, user_id, call_id, expected_status_code=200):
        """
        会話履歴取得APIをテスト
        
        Args:
            user_id (str): ユーザーID
            call_id (str): 呼び出しID
            expected_status_code (int): 期待するHTTPステータスコード
        """
        url = f"{self.base_url}/get-conversation-history"
        payload = {
            "userID": user_id,
            "callID": call_id
        }
        
        try:
            print(f"\n📡 API テスト: {user_id} / {call_id}")
            print(f"URL: {url}")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            response = requests.post(url, json=payload, timeout=10)
            
            print(f"ステータスコード: {response.status_code} (期待値: {expected_status_code})")
            
            status_match = response.status_code == expected_status_code
            if status_match:
                print("✅ ステータスコードが期待値と一致")
            else:
                print("❌ ステータスコードが期待値と異なります")
            
            # レスポンス内容を表示（簡略化）
            try:
                response_data = response.json()
                print(f"レスポンスステータス: {response_data.get('status', 'N/A')}")
                
                # 成功時の詳細情報表示
                if response_data.get('status') == 'success':
                    user_info = response_data.get('user_info', {})
                    conversation = response_data.get('conversation', {})
                    print(f"📊 取得結果:")
                    print(f"  ユーザー名: {user_info.get('name', 'N/A')}")
                    print(f"  会話数: {len(conversation.get('conversation', []))}")
                    print(f"  会話時間: {conversation.get('duration_seconds', 'N/A')}秒")
                    print(f"  気分: {conversation.get('analysis', {}).get('mood', 'N/A')}")
                elif response_data.get('status') == 'error':
                    print(f"エラーコード: {response_data.get('error_code', 'N/A')}")
                    print(f"エラーメッセージ: {response_data.get('message', 'N/A')}")
                
            except json.JSONDecodeError:
                print(f"JSONデコードエラー: {response.text[:100]}...")
                status_match = False
            
            return response, status_match
            
        except requests.RequestException as e:
            print(f"❌ リクエストエラー: {str(e)}")
            return None, False
    
    def test_health_check(self):
        """ヘルスチェックテスト"""
        url = f"{self.base_url}/health"
        try:
            print(f"\n🏥 ヘルスチェック: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print("✅ サービス正常稼働中")
                return True
            else:
                print(f"❌ サービス異常: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ サービス接続エラー: {str(e)}")
            return False
    
    def run_all_tests(self):
        """全テストケースを実行"""
        print("=" * 60)
        print("会話履歴取得API 総合テスト")
        print("=" * 60)
        
        # ヘルスチェック
        if not self.test_health_check():
            print("❌ サービスが起動していません。テストを中止します。")
            return
        
        # テストケース群
        test_cases = [
            {
                "name": "正常ケース - user001 朝の会話",
                "user_id": "user001",
                "call_id": "call_001_20241201_morning",
                "expected_status": 200
            },
            {
                "name": "正常ケース - user001 夜の会話",
                "user_id": "user001", 
                "call_id": "call_001_20241201_evening",
                "expected_status": 200
            },
            {
                "name": "正常ケース - user002 朝の会話",
                "user_id": "user002",
                "call_id": "call_002_20241201_morning",
                "expected_status": 200
            },
            {
                "name": "エラーケース - 存在しないユーザー",
                "user_id": "user999",
                "call_id": "call_001_20241201_morning",
                "expected_status": 404
            },
            {
                "name": "エラーケース - 存在しないcallID",
                "user_id": "user001",
                "call_id": "call_invalid_999",
                "expected_status": 404
            },
            {
                "name": "エラーケース - ユーザーIDミスマッチ",
                "user_id": "user002",
                "call_id": "call_001_20241201_morning",
                "expected_status": 403
            }
        ]
        
        print(f"\n📋 実行予定のテストケース: {len(test_cases)}件")
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'-' * 50}")
            print(f"テストケース {i}/{len(test_cases)}: {test_case['name']}")
            print(f"{'-' * 50}")
            
            response, is_success = self.test_get_conversation_history(
                test_case["user_id"],
                test_case["call_id"],
                test_case["expected_status"]
            )
            
            if is_success:
                success_count += 1
                print("✅ テストケース合格")
            else:
                print("❌ テストケース不合格")
            
            # 次のテストまで少し待機
            time.sleep(0.5)
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)
        print(f"実行したテスト数: {len(test_cases)}")
        print(f"成功: {success_count}")
        print(f"失敗: {len(test_cases) - success_count}")
        print(f"成功率: {success_count / len(test_cases) * 100:.1f}%")
        
        if success_count == len(test_cases):
            print("🎉 全てのテストが成功しました！")
        else:
            print("⚠️  一部のテストが失敗しています。")

if __name__ == "__main__":
    # テスト実行
    tester = ConversationHistoryAPITester()
    tester.run_all_tests() 