"""通話内容をチェックするクラス"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel

from repositories.firestore_call_repository import FirestoreCallRepository
from repositories.firestore_call_check_repository import FirestoreCallCheckRepository
from repositories.webhook_notification_repository import WebhookNotificationRepository
from models.call import Call
from models.call_check import CallCheckResult, OpenAICallAnalysisResult, SeverityLevel, Evidence

logger = logging.getLogger(__name__)


class CallChecker:
    """通話内容をチェックするクラス"""

    def __init__(self, project_id: Optional[str] = None):
        """
        Args:
            project_id: GCPプロジェクトID
        """
        self.call_repository = FirestoreCallRepository(project_id)
        self.check_repository = FirestoreCallCheckRepository(project_id)
        self.notification_repository = WebhookNotificationRepository()
        self.openai_client = OpenAI()

    async def check_user_calls(self, user_id: str, n: Optional[int] = 10, save_result: bool = True) -> tuple[CallCheckResult, Optional[str]]:
        """
        指定ユーザーの直近の通話内容をチェック

        Args:
            user_id: チェック対象のユーザーID
            n: 分析する直近の通話数（デフォルト: 10件）
            save_result: 結果をFirestoreに保存するか（デフォルト: True）

        Returns:
            tuple[CallCheckResult, Optional[str]]: (チェック結果, チェックID)
        """
        try:
            # 通話データを取得（直近n件）
            calls = await self.call_repository.get_latest_calls(user_id, n)

            if not calls:
                result = CallCheckResult(
                    reason="分析対象の通話データが見つかりませんでした",
                    severity_level=SeverityLevel.NORMAL,
                    detected_issues=[],
                    evidence=[],
                    source_calls=[],
                    analyzed_at=datetime.now()
                )

                # 通話データがない場合は保存しない
                return result, None

            # OpenAIで分析
            analysis_result = await self._analyze_with_openai(calls)

            call_ids = [call.call_id for call in calls]

            result = CallCheckResult(
                reason=analysis_result.reason,
                severity_level=analysis_result.severity_level,
                detected_issues=analysis_result.detected_issues,
                evidence=analysis_result.evidence,
                source_calls=call_ids,
                analyzed_at=datetime.now()
            )

            check_id = None
            if save_result:
                check_id = await self.check_repository.save_check_result(user_id, result)

            # 異常時の通知送信
            await self._send_notification_if_needed(user_id, result)

            return result, check_id

        except Exception as e:
            logger.error(f"通話チェックエラー user_id: {user_id}, error: {e}")
            result = CallCheckResult(
                reason=f"通話チェック中にエラーが発生しました: {str(e)}",
                severity_level=SeverityLevel.NORMAL,
                detected_issues=[],
                evidence=[],
                source_calls=[],
                analyzed_at=datetime.now()
            )

            check_id = None
            if save_result:
                try:
                    check_id = await self.check_repository.save_check_result(user_id, result)
                except:
                    pass  # エラー時は保存失敗しても続行

            return result, check_id

    async def _analyze_with_openai(self, calls: List[Call]) -> OpenAICallAnalysisResult:
        """OpenAI GPT-4o-miniで通話内容を分析"""
        try:
            # 分析用のプロンプトを作成
            analysis_prompt = self._create_analysis_prompt(calls)

            # デバッグ用：プロンプトをログ出力
            logger.debug("=== OpenAI分析プロンプト開始 ===")
            logger.debug(f"通話数: {len(calls)}件")
            logger.debug(f"プロンプト:\n{analysis_prompt}")
            logger.debug("=== OpenAI分析プロンプト終了 ===")

            # OpenAI APIを呼び出し（Pydantic response_formatを使用）
            response = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたは高齢者の安否確認通話を分析する専門家です。

【重要な分析方針】
最新の状態を最も重視してください。過去に深刻な発言があっても、最新の通話で改善が見られる場合は、現在の状態で判定してください。

【通話内容の読み方】
- 通話は時系列順（古い→新しい）で表示されています
- 各通話内の発言も時系列順です
- 通話の文字起こしは、誤字が混じっている場合がありますが、文脈で正しい発言に読み替えてください

【判定の原則】
1. 最新の通話での状態を最優先に考慮
2. 過去の問題が最新通話で改善している場合は、低い重要度に判定
3. 継続的または悪化している問題のみ高い重要度に判定

自治体担当者への通報は緊急性の高い場合のみに限定されるため、以下の重大な問題のみを検出してください：

【異常】緊急対応が必要な事案：
1. 生命に関わる健康問題（倒れた、動けない、激しい痛み、呼吸困難など）
2. 重度の認知機能障害（自分の名前や場所がわからない、家族を認識できないなど）
3. 虐待や犯罪被害の疑い
4. 自殺念慮や自傷行為の兆候


【要観察】継続的な観察が必要な事案：
- 軽度〜中度の認知機能低下（物忘れが増えている、同じ話を繰り返すなど）
- 慢性的な体調不良（食欲低下、睡眠障害、疲労感など）
- 孤立感や軽度の抑うつ状態
- 日常生活に支障が出始めている（買い物が困難、家事ができないなど）

【通常】問題なし、または一時的な問題：
- 一時的な体調不良（風邪、軽い頭痛など）
- 普通の寂しさや愚痴
- 軽度の生活上の不便

severity_levelを判定してください。

判断の根拠となった具体的な発言を必ず引用してください。各引用には通話IDと発言者を含めてください。"""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format=OpenAICallAnalysisResult
            )

            # Pydanticモデルが直接返される
            return response.choices[0].message.parsed

        except Exception as e:
            logger.error(f"OpenAI分析エラー: {e}")
            return OpenAICallAnalysisResult(
                reason="分析中にエラーが発生しました",
                severity_level=SeverityLevel.NORMAL,
                detected_issues=[],
                evidence=[]
            )

    def _create_analysis_prompt(self, calls: List[Call]) -> str:
        """分析用のプロンプトを作成"""
        prompt_parts = ["以下の通話内容を分析してください。発言を引用する際は、必ず通話IDを含めてください：\n"]

        # 古い順に並び替え（時系列順）
        sorted_calls = sorted(calls, key=lambda c: c.call_started_at)

        for i, call in enumerate(sorted_calls, 1):
            call_date = call.call_started_at.strftime("%Y-%m-%d %H:%M")
            # 最新の通話かどうかを明示
            time_note = " (最新)" if i == len(sorted_calls) else ""
            prompt_parts.append(
                f"\n【通話 {i}】 通話ID: {call.call_id}, 日時: {call_date}{time_note}")

            for msg in call.transcriptions:
                speaker_label = "利用者" if msg.speaker == "user" else "オペレーター"
                prompt_parts.append(f"{speaker_label}: {msg.text}")

        return "\n".join(prompt_parts)

    async def _send_notification_if_needed(self, user_id: str, result: CallCheckResult) -> None:
        """
        必要に応じて通知を送信

        Args:
            user_id: ユーザーID
            result: 通話チェック結果
        """
        try:
            # 環境変数から通知対象の最小レベルを取得（デフォルト: ABNORMAL=異常のみ）
            min_level_name = os.getenv("NOTIFICATION_MIN_LEVEL", "ABNORMAL")
            min_notification_level = getattr(
                SeverityLevel, min_level_name, SeverityLevel.ABNORMAL)

            # 指定レベル以上の場合のみ通知
            if result.severity_level.level >= min_notification_level.level:
                notification_result = await self.notification_repository.send_call_check_notification(user_id, result)

                if notification_result.get("success"):
                    logger.info(
                        f"通知成功: user_id={user_id}, severity_level={result.severity_level}")
                else:
                    logger.warning(
                        f"通知失敗: user_id={user_id}, severity_level={result.severity_level}")
            else:
                logger.debug(
                    f"通知対象外: user_id={user_id}, severity_level={result.severity_level} (対象: {notification_levels})")

        except Exception as e:
            logger.error(
                f"通知処理エラー: user_id={user_id}, error={e}", exc_info=True)
