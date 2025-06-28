"""
Gemini APIを使用した日記生成サービス
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai

logger = logging.getLogger(__name__)

class DiaryGenerator:
    """
    Gemini APIを使用して日記風の文章を生成するクラス
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        DiaryGenerator初期化
        
        Args:
            api_key: Gemini API キー（指定しない場合は環境変数から取得）
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Gemini APIの設定
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini client initialized successfully")
    
    def generate_diary_entry(
        self, 
        user_info: Dict[str, Any], 
        conversation_history: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        ユーザー情報と会話履歴から日記風の文章を生成
        
        Args:
            user_info: ユーザー情報辞書
            conversation_history: 会話履歴辞書
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (成功フラグ, 生成された日記, エラーメッセージ)
        """
        try:
            # ユーザー情報の抽出
            user_name = self._extract_user_name(user_info)
            user_details = self._format_user_details(user_info)
            
            # 会話履歴の整形
            conversation_text = self._format_conversation_history(conversation_history)
            
            if not conversation_text:
                return False, None, "会話履歴が見つかりません"
            
            # プロンプト生成
            prompt = self._create_diary_prompt(user_name, user_details, conversation_text)
            
            # Gemini API呼び出し
            response = self.model.generate_content(prompt)
            
            diary_text = response.text.strip()
            
            if not diary_text:
                return False, None, "Gemini APIから空のレスポンスが返されました"
            
            logger.info(f"Diary generated successfully for user: {user_name}")
            return True, diary_text, None
            
        except Exception as e:
            error_msg = f"日記生成中にエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _extract_user_name(self, user_info: Dict[str, Any]) -> str:
        """ユーザー名を抽出"""
        # 様々な形式のユーザー名フィールドに対応
        for field in ['name', 'full_name', 'last_name', 'first_name']:
            if field in user_info and user_info[field]:
                return user_info[field]
        
        # last_name + first_nameの組み合わせ
        if 'last_name' in user_info and 'first_name' in user_info:
            return f"{user_info['last_name']} {user_info['first_name']}"
        
        # userIDをフォールバック
        return user_info.get('user_id', '利用者')
    
    def _format_user_details(self, user_info: Dict[str, Any]) -> str:
        """ユーザー詳細情報をフォーマット"""
        details = []
        
        # 基本情報
        if 'birth_date' in user_info:
            try:
                # 年齢計算（簡易版）
                birth_date = user_info['birth_date']
                if isinstance(birth_date, str):
                    birth_year = int(birth_date[:4])
                    current_year = datetime.now().year
                    age = current_year - birth_year
                    details.append(f"年齢: {age}歳")
            except:
                pass
        
        # 住所情報
        address_parts = []
        for field in ['prefecture', 'address_block', 'address_building']:
            if field in user_info and user_info[field]:
                address_parts.append(user_info[field])
        
        if address_parts:
            details.append(f"住所: {''.join(address_parts)}")
        
        return '\n'.join(details) if details else ""
    
    def _format_conversation_history(self, conversation_history: Dict[str, Any]) -> str:
        """会話履歴を読みやすい形式にフォーマット"""
        try:
            # Firestoreから取得される実際の構造に対応
            # conversation_history -> conversation_history -> conversation の順でアクセス
            nested_history = conversation_history.get('conversation_history', {})
            conversations = nested_history.get('conversation', [])
            
            # 直接conversationフィールドがある場合もチェック
            if not conversations:
                conversations = conversation_history.get('conversation', [])
            
            if not conversations:
                logger.warning("会話履歴が見つかりません")
                return ""
            
            formatted_lines = []
            for conv in conversations:
                if isinstance(conv, dict):
                    # Firestoreの実際の構造: speaker, message フィールド
                    speaker = conv.get('speaker', '')
                    message = conv.get('message', '')
                    
                    if speaker and message:
                        speaker_label = 'AI' if speaker.lower() in ['ai', 'assistant'] else 'ユーザー'
                        formatted_lines.append(f"{speaker_label}: {message}")
                    
                    # 旧形式のサポート: role, text フィールド
                    elif 'role' in conv and 'text' in conv:
                        role = conv.get('role', '')
                        text = conv.get('text', '')
                        role_label = 'AI' if role == 'assistant' else 'ユーザー'
                        formatted_lines.append(f"{role_label}: {text}")
                    
                    # messageのみの場合
                    elif message:
                        formatted_lines.append(message)
                        
                elif isinstance(conv, str):
                    formatted_lines.append(conv)
            
            if not formatted_lines:
                logger.warning("フォーマット可能な会話データが見つかりません")
                return ""
                
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"会話履歴のフォーマット中にエラー: {e}")
            # デバッグ用に構造を出力
            logger.debug(f"会話履歴の構造: {conversation_history}")
            return ""
    
    def _create_diary_prompt(self, user_name: str, user_details: str, conversation_text: str) -> str:
        """日記生成用プロンプトを作成"""
        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        prompt = f"""
以下のユーザー情報と今日の会話内容をもとに、家族向けの温かい日記風の文章を作成してください。

【ユーザー情報】
名前: {user_name}
{user_details}

【今日の会話内容】
{conversation_text}

【日記作成の要件】
1. 家族が読んで安心できる、温かみのある内容にしてください
2. 敬語は使わず、親しみやすい文体で書いてください
3. 200-300文字程度でまとめてください
4. 「{current_date} {user_name}さんの一日」というタイトルで始めてください
5. ユーザーの健康状態や気持ち、活動内容を中心に書いてください
6. ネガティブな内容があっても、前向きな表現に変換してください
7. プライベートすぎる情報は含めず、家族が読んでほっこりする内容にしてください

【出力形式】
タイトル: {current_date} {user_name}さんの一日

（本文）
"""
        
        return prompt
    
    def test_generation(self) -> bool:
        """API接続テスト用の簡単な生成テスト"""
        try:
            # 簡単なテストプロンプト
            test_prompt = "こんにちは。今日はいい天気ですね。"
            response = self.model.generate_content(test_prompt)
            
            if response.text and len(response.text.strip()) > 0:
                print("✅ Gemini API接続テスト成功")
                print(f"📄 レスポンス: {response.text[:100]}...")
                return True
            else:
                print("❌ Gemini APIから空のレスポンスが返されました")
                return False
                
        except Exception as e:
            print(f"❌ Gemini APIテスト実行エラー: {str(e)}")
            return False 