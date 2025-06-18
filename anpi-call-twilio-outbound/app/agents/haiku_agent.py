import os
from typing import Dict, Any
from openai import OpenAI


class HaikuAgent:
    """俳句を作成するエージェント"""

    def __init__(self):
        self.name = "俳句エージェント"
        if OpenAI:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = None

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """俳句を生成する"""
        context = input_data.get("context", "")

        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not available",
                "agent": self.name
            }

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは優れた俳句詩人です。相手の状況や気持ちを汲み取って、心に響く俳句を詠んでください。必ず5-7-5の形式で一句のみ返してください。"
                    },
                    {
                        "role": "user",
                        "content": f"次の文脈に基づいて俳句を詠んでください: {context}"
                    }
                ],
                temperature=0.8,
                max_tokens=100
            )

            haiku = response.choices[0].message.content.strip()

            return {
                "success": True,
                "haiku": haiku,
                "agent": self.name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
