#!/usr/bin/env python3
"""
AI Diary Service 直接テスト（サーバー不要）
DB接続とGemini API呼び出しを含む完全なテスト
"""

import os
import sys

# テスト用パラメータ
TEST_USER_ID = "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
TEST_CALL_ID = "CA995a950a2b9f6623a5adc987d0b31131"

def test_db_connection():
    """DB接続テスト"""
    print("🔄 DB接続テストを開始します...")
    
    try:
        from get_info.db_connection import test_connection
        success, message = test_connection()
        
        if success:
            print("✅ DB接続テスト成功!")
            print(f"   メッセージ: {message}")
            return True
        else:
            print(f"❌ DB接続テスト失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ DB接続テスト中にエラーが発生しました: {str(e)}")
        return False

def test_user_info_retrieval():
    """ユーザー情報取得テスト"""
    print(f"\n🔄 ユーザー情報取得テストを開始します (userID: {TEST_USER_ID})...")
    
    try:
        from get_info.user_service import get_user_info
        
        success, user_info, error_code = get_user_info(TEST_USER_ID)
        
        if success:
            print("✅ ユーザー情報取得成功!")
            print(f"   取得されたユーザー情報:")
            for key, value in user_info.items():
                print(f"     {key}: {value}")
            return True, user_info
        else:
            print(f"❌ ユーザー情報取得失敗: エラーコード {error_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ ユーザー情報取得テスト中にエラーが発生しました: {str(e)}")
        return False, None

def test_conversation_history():
    """会話履歴取得テスト"""
    print(f"\n🔄 会話履歴取得テストを開始します (userID: {TEST_USER_ID}, callID: {TEST_CALL_ID})...")
    
    try:
        from get_history.conversation_service import get_conversation_history
        
        success, conversation_data, error_code = get_conversation_history(TEST_USER_ID, TEST_CALL_ID)
        
        if success:
            print("✅ 会話履歴取得成功!")
            print(f"   取得された会話履歴:")
            if 'conversation' in conversation_data:
                for i, conv in enumerate(conversation_data['conversation'][:3]):  # 最初の3件のみ表示
                    print(f"     {i+1}. {conv.get('role', 'unknown')}: {conv.get('text', '')[:50]}...")
                if len(conversation_data['conversation']) > 3:
                    print(f"     ... 他 {len(conversation_data['conversation']) - 3} 件")
            return True, conversation_data
        else:
            print(f"❌ 会話履歴取得失敗: エラーコード {error_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ 会話履歴取得テスト中にエラーが発生しました: {str(e)}")
        return False, None

def test_diary_generation_with_real_data(user_info, conversation_data):
    """実データを使用した日記生成テスト"""
    print("\n🔄 実データを使用した日記生成テストを開始します...")
    
    try:
        from create_diary_entry import DiaryGenerator
        
        generator = DiaryGenerator()
        success, diary_text, error = generator.generate_diary_entry(user_info, conversation_data)
        
        if success:
            print("✅ 日記生成テスト成功!")
            print("\n📄 生成された日記:")
            print("=" * 60)
            print(diary_text)
            print("=" * 60)
            return True
        else:
            print(f"❌ 日記生成テスト失敗: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 日記生成テスト中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("🚀 AI Diary Service 直接テスト")
    print("=" * 50)
    print(f"テスト対象:")
    print(f"  userID: {TEST_USER_ID}")
    print(f"  callID: {TEST_CALL_ID}")
    print("=" * 50)
    
    # 環境変数チェック
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        print("   以下のコマンドで設定してください:")
        print("   export GEMINI_API_KEY='your_api_key_here'")
        return 1
    
    test_results = []
    
    # 1. DB接続テスト
    test_results.append(test_db_connection())
    
    # 2. ユーザー情報取得テスト
    user_success, user_info = test_user_info_retrieval()
    test_results.append(user_success)
    
    # 3. 会話履歴取得テスト
    conv_success, conversation_data = test_conversation_history()
    test_results.append(conv_success)
    
    # 4. 日記生成テスト（実データ使用）
    if user_success and conv_success:
        diary_success = test_diary_generation_with_real_data(user_info, conversation_data)
        test_results.append(diary_success)
    else:
        print("\n⏭️  ユーザー情報または会話履歴の取得に失敗したため、日記生成テストをスキップします")
        test_results.append(False)
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー:")
    print(f"  1. DB接続: {'✅' if test_results[0] else '❌'}")
    print(f"  2. ユーザー情報取得: {'✅' if test_results[1] else '❌'}")
    print(f"  3. 会話履歴取得: {'✅' if test_results[2] else '❌'}")
    print(f"  4. 日記生成 (実データ): {'✅' if test_results[3] else '❌'}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    
    if success_count == total_count:
        print(f"\n🎉 すべてのテストが成功しました! ({success_count}/{total_count})")
        return 0
    else:
        print(f"\n⚠️  一部のテストが失敗しました: {success_count}/{total_count} 成功")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
