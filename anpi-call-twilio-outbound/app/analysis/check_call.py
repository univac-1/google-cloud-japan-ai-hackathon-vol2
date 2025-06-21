"""通話内容をチェックするクラス"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from openai import OpenAI
from pydantic import BaseModel

from repositories.firestore_call_repository import FirestoreCallRepository
from repositories.firestore_call_check_repository import FirestoreCallCheckRepository
from models.call_check import CallCheckResult, OpenAICallAnalysisResult

logger = logging.getLogger(__name__)


class CallChecker:
    """通話内容をチェックするクラス"""

    def __init__(self, project_id: Optional[str] = None, max_calls: int = 5):
        """
        Args:
            project_id: GCPプロジェクトID
            max_calls: 分析する最大通話数（デフォルト: 5件）
        """
        self.max_calls = max_calls
        self.call_repository = FirestoreCallRepository(project_id)
        self.check_repository = FirestoreCallCheckRepository(project_id)
        self.openai_client = OpenAI()

    async def check_user_calls(self, user_id: str, days: int = 7, save_result: bool = True) -> tuple[CallCheckResult, Optional[str]]:
        """
        指定ユーザーの通話内容をチェック

        Args:
            user_id: チェック対象のユーザーID
            days: チェック期間（日数、デフォルト: 7日）
            save_result: 結果をFirestoreに保存するか（デフォルト: True）

        Returns:
            tuple[CallCheckResult, Optional[str]]: (チェック結果, チェックID)
        """
        try:
            # 最近の通話データを取得
            calls = await self.call_repository.get_recent_calls(user_id, days, self.max_calls)

            if not calls:
                result = CallCheckResult(
                    has_issue=False,
                    reason="分析対象の通話データが見つかりませんでした",
                    confidence=0.0,
                    detected_issues=[],
                    analyzed_calls=[],
                    sources=[]
                )
                
                # 通話データがない場合は保存しない
                return result, None

            # OpenAIで分析
            analysis_result = await self._analyze_with_openai(calls)

            call_ids = [call.get("call_id", "") for call in calls]
            
            result = CallCheckResult(
                has_issue=analysis_result["has_issue"],
                reason=analysis_result["reason"],
                confidence=analysis_result["confidence"],
                detected_issues=analysis_result["detected_issues"],
                analyzed_calls=call_ids,
                sources=call_ids
            )
            
            check_id = None
            if save_result:
                check_id = await self.check_repository.save_check_result(user_id, result)
            
            return result, check_id

        except Exception as e:
            logger.error(f"通話チェックエラー user_id: {user_id}, error: {e}")
            result = CallCheckResult(
                has_issue=False,
                reason=f"通話チェック中にエラーが発生しました: {str(e)}",
                confidence=0.0,
                detected_issues=[],
                analyzed_calls=[],
                sources=[]
            )
            
            check_id = None
            if save_result:
                try:
                    check_id = await self.check_repository.save_check_result(user_id, result)
                except:
                    pass  # エラー時は保存失敗しても続行
            
            return result, check_id

    async def _analyze_with_openai(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OpenAI GPT-4o-miniで通話内容を分析"""
        try:
            # 分析用のプロンプトを作成
            analysis_prompt = self._create_analysis_prompt(calls)

            # OpenAI APIを呼び出し
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたは高齢者の安否確認通話を分析する専門家です。
通話内容から以下の問題を検出してください：
1. 健康状態の悪化
2. 認知機能の低下
3. 日常生活の問題
4. 孤立感や抑うつ状態
5. 安全上の懸念

結果はJSON形式で返してください：
{
  "has_issue": boolean,
  "reason": "問題の要約",
  "confidence": 0.0-1.0,
  "detected_issues": ["具体的な問題1", "具体的な問題2"]
}"""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            # レスポンスを解析
            result_text = response.choices[0].message.content
            result = eval(result_text)  # JSONをパース

            return result

        except Exception as e:
            logger.error(f"OpenAI分析エラー: {e}")
            return {
                "has_issue": False,
                "reason": "分析中にエラーが発生しました",
                "confidence": 0.0,
                "detected_issues": []
            }

    def _create_analysis_prompt(self, calls: List[Dict[str, Any]]) -> str:
        """分析用のプロンプトを作成"""
        prompt_parts = ["以下の通話内容を分析してください：\n"]

        for i, call in enumerate(calls, 1):
            call_date = call.get("call_started_at", "不明")
            transcriptions = call.get("transcriptions", [])

            if isinstance(call_date, datetime):
                call_date = call_date.strftime("%Y-%m-%d %H:%M")

            prompt_parts.append(f"\n【通話 {i}】 日時: {call_date}")

            for msg in transcriptions:
                speaker = "利用者" if msg.get("speaker") == "user" else "オペレーター"
                text = msg.get("text", "")
                prompt_parts.append(f"{speaker}: {text}")

        return "\n".join(prompt_parts)
