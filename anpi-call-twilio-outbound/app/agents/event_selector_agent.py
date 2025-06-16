import logging
import os
from typing import Dict, Any
from datetime import date
from agents.base_agent import BaseAgent
from models.schemas import User, Event
from openai import OpenAI

logger = logging.getLogger(__name__)


class EventSelectorAgent(BaseAgent):
    """イベント選定専門エージェント - OpenAI APIを使用"""

    def __init__(self):
        super().__init__("イベント選定エージェント")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key) if OpenAI else None

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Event selector input: {input_data}")
        """
        高齢者の好みに合うイベントを選定する

        Args:
            input_data: {
                "user": User型の高齢者情報,
                "conversation": 会話内容,
                "events": List[Event]型のイベントリスト,
                "count": 提案数
            }

        Returns:
            {
                "success": bool,
                "selected_events": [
                    {
                        "event": Event,
                        "reason": 選定理由
                    },
                    ...
                ]
            }
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not available"
            }

        user = User(**input_data["user"])
        conversation = input_data.get("conversation", "")
        events = [Event(**event) for event in input_data["events"]]
        count = input_data.get("count", 3)

        # イベント情報を文字列化
        events_text = "\n\n".join([
            f"イベントID: {event.event_id}\n"
            f"タイトル: {event.title}\n"
            f"説明: {event.description}\n"
            f"開催日時: {event.start_datetime.strftime('%Y年%m月%d日 %H:%M')} - {event.end_datetime.strftime('%H:%M')}\n"
            f"場所: {event.prefecture}{event.address_block}{event.address_building or ''}"
            for event in events
        ])

        # プロンプト作成
        prompt = f"""
以下の高齢者の情報と会話内容を基に、提供されたイベントリストの中から最も適したイベントを{count}個選んでください。

【高齢者情報】
- 氏名: {user.last_name} {user.first_name}様
- 年齢: {self._calculate_age(user.birth_date)}歳
- 性別: {'男性' if user.gender == 'male' else '女性'}
- 居住地: {user.prefecture}

【会話内容】
{conversation if conversation else '特になし'}

【イベントリスト】
{events_text}

【選定基準】
1. 高齢者の年齢や体力を考慮
2. 会話内容から読み取れる興味・関心との関連性
3. 開催場所へのアクセスのしやすさ
4. イベントの内容が高齢者に適しているか

以下の形式で回答してください：
1. [イベントID] - [選定理由を50文字程度で説明]
2. [イベントID] - [選定理由を50文字程度で説明]
3. [イベントID] - [選定理由を50文字程度で説明]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは高齢者の生活を支援する優しいアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # レスポンスをパース
            result_text = response.choices[0].message.content
            selected_events = []

            # イベントIDをキーとした辞書を作成
            event_dict = {event.event_id: event for event in events}

            # 結果をパース（重複除去）
            added_event_ids = set()
            for line in result_text.strip().split('\n'):
                if line.strip():
                    # 番号を削除してパース
                    line = line.strip()
                    if '. ' in line:
                        line = line.split('. ', 1)[1]

                    if ' - ' in line:
                        event_id, reason = line.split(' - ', 1)
                        event_id = event_id.strip()

                        if event_id in event_dict and event_id not in added_event_ids:
                            selected_events.append({
                                "event": event_dict[event_id].model_dump(),
                                "reason": reason.strip()
                            })
                            added_event_ids.add(event_id)
            logger.info(f"Event selector result: {selected_events}")

            return {
                "success": True,
                "selected_events": selected_events[:count]  # 指定数に制限
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"イベント選定エラー: {str(e)}"
            }

    def _calculate_age(self, birth_date: date) -> int:
        """生年月日から年齢を計算"""
        from datetime import date as datetime_date
        today = datetime_date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
