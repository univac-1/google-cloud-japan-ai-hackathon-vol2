#!/usr/bin/env python3
"""
完全な一連の処理（ユーザー情報取得→会話履歴取得→日記生成→挿絵作成）のテストスクリプト
"""

import requests
import json
import sys

def test_complete_diary_generation(base_url="http://localhost:8080"):
    """
    完全な日記生成APIをテストする
    """
    url = f"{base_url}/generate-diary"
    
    # テストデータ（指定パラメータ）
    test_data = {
        "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
        "callID": "CA995a950a2b9f6623a5adc987d0b31131"
    }
    
    print("=== 完全な日記生成APIテスト ===")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(url, json=test_data, timeout=120)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            if data.get('illustrationUrl'):
                print("\n✅ 挿絵URLが正常に生成されました!")
                print(f"挿絵URL: {data['illustrationUrl']}")
            else:
                print("\n⚠️ 挿絵URLがnullです（生成に失敗した可能性があります）")
                
            if data.get('diary'):
                print(f"\n📝 生成された日記: {data['diary'][:100]}...")
            
            return True
        else:
            print(f"\n❌ APIエラー: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ リクエストがタイムアウトしました")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return False
    except json.JSONDecodeError:
        print("❌ JSONレスポンスの解析に失敗しました")
        print(f"Raw response: {response.text}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    success = test_complete_diary_generation(base_url)
    sys.exit(0 if success else 1)
