import os
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.event_selector_agent import EventSelectorAgent
from models.schemas import User, Event
from repositories.cloudsql_event_repository import CloudSQLEventRepository


class EventAgent(BaseAgent):
    """高齢者におすすめのイベントを提案するエージェント"""

    def __init__(self, event_data_path: str = None, max_filter_count: int = 100):
        super().__init__("イベント提案エージェント")
        self.event_selector = EventSelectorAgent()
        # CloudSQLEventRepositoryを使用
        self.event_repository = CloudSQLEventRepository()
        self.max_filter_count = max_filter_count

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        高齢者におすすめのイベントを提案する

        Args:
            input_data: {
                "user": 高齢者の情報（User型）,
                "conversation": 高齢者との会話内容,
                "count": 提案数（デフォルト: 3）
            }

        Returns:
            {
                "success": bool,
                "events": 提案するイベントのリスト（根拠付き）
            }
        """
        try:
            # 入力データを検証
            user_data = input_data.get("user")
            if not user_data:
                return {
                    "success": False,
                    "error": "ユーザー情報が提供されていません"
                }

            # User型に変換
            user = User(**user_data)
            conversation = input_data.get("conversation", "")
            count = input_data.get("count", 3)

            # 1. 高齢者の県を取得
            user_prefecture = user.prefecture

            # 2. EventRepositoryから条件に一致するイベントを取得
            filtered_events = await self.event_repository.get_upcoming_events_by_prefecture(
                user_prefecture,
                weeks_ahead_min=1,
                weeks_ahead_max=4,
                max_count=self.max_filter_count
            )

            if not filtered_events:
                return {
                    "success": True,
                    "events": [],
                    "message": f"{user_prefecture}で開催予定のイベントが見つかりませんでした"
                }

            # 3. イベント選定エージェントに処理を委譲
            selector_result = await self.event_selector.process({
                "user": user_data,
                "conversation": conversation,
                "events": [event.model_dump() for event in filtered_events],
                "count": count
            })

            if not selector_result["success"]:
                return selector_result

            return {
                "success": True,
                "events": selector_result["selected_events"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"イベント提案処理エラー: {str(e)}"
            }
