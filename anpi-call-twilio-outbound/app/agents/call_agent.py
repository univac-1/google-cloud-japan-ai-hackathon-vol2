import os
import json
import base64
import asyncio
import logging
from typing import Dict, Any, Optional
import websockets
from websockets.protocol import State
from agents.base_agent import BaseAgent
from agents.haiku_agent import HaikuAgent
from agents.event_agent import EventAgent
from agents.event_selector_agent import EventSelectorAgent
from models.openai_event_types import OpenAIEventType
from models.server_event_types import ServerEventType
from repositories.cloudsql_user_repository import CloudSQLUserRepository
from models.schemas import User


logger = logging.getLogger(__name__)


class CallAgent(BaseAgent):
    """通話エージェント - OpenAI Realtime APIを使用"""

    def __init__(self):
        super().__init__("通話エージェント")
        self.user_id = None
        # CloudSQLUserRepositoryを使用
        self.user_repository = CloudSQLUserRepository()
        self.user: Optional[User] = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_ws: Optional[Any] = None
        self.haiku_agent = HaikuAgent()
        self.event_agent = EventAgent()
        self.event_selector_agent = EventSelectorAgent()
        self.conversation_history = []
        self.accumulated_audio = bytearray()
        self.session_ready = False
        self.last_assistant_item = None
        self.stored_events = []  # イベント情報を保存
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}")

    async def connect_to_openai(self):
        """OpenAI Realtime APIに接続"""
        if not websockets:
            raise RuntimeError("websockets library not available")

        if not self.openai_ws or self.openai_ws.state == State.CLOSED:
            self.openai_ws = await websockets.connect(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                additional_headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
            )
            await self._initialize_session()

    async def _initialize_session(self):
        """OpenAIセッションの初期化（ベース設定）"""
        session_config = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 3000
                },
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {"model": "whisper-1"},
                "voice": "alloy",
                "instructions": """あなたは高齢者の見守りサービスの通話エージェントです。

                【目的】
                - 高齢者の異常や困りごとに気づくこと
                - 高齢者が孤立しないよう、会話を通じた心のケアを行うこと
                - 自治体が提供するイベント情報を、無理なく案内すること

                【会話スタイル】
                - 詰問や説教口調は避け、あたたかく丁寧な言葉づかいを使うこと
                - 会話は一方的にならないよう、相手の返答を想定して区切ること
                - 内容が機械的すぎたり、無感情にならないよう配慮すること
                - 「〜ですね」「〜ですか？」など、親しみやすい敬語を使うこと

                【会話の流れ（目安）】
                1. あいさつと健康状態の確認
                   - 「こんにちは。見守りのご連絡でお電話しました。今日もお元気でいらっしゃいますか？」から始める
                   - 体調や天候について軽く触れる
                
                2. 食事や生活の様子の話題
                   - 食事内容や食欲について尋ねる
                   - 水分補給や室温管理など、季節に応じた健康管理について話す
                
                3. ご近所や家族との交流確認
                   - 最近の家族やご近所との交流について尋ねる
                   - 孤立していないか、寂しさを感じていないか確認する
                
                4. 直近の地域イベントの案内
                   - 会話の流れで自然にイベント情報を提供する
                   - search_events関数を使って適切なイベントを紹介する
                   - 無理強いせず、「よろしければ」という表現を使う
                
                5. しめくくりと次回予告
                   - 「またお話できるのを楽しみにしていますね」
                   - 「どうかご自愛ください」
                   - 相手が心配事を口にした場合は、適切に対応する

                【ツール使用ルール】
                - 俳句をリクエストされた場合は、request_haiku関数を呼び出す
                - イベント案内の段階で、search_events関数を呼び出してイベント概要を取得する
                - ユーザーが特定のイベントに興味を示したら、get_event_details関数で番号や曖昧な表現で詳細を取得する
                - ツール呼び出し前に「少々お待ちください」など一言添える

                【重要な注意事項】
                - 相手の発言に異常（体調不良、生活の困難、精神的な不安など）を感じたら、優先的に対応する
                - 長時間話を聞いてほしそうな場合は、丁寧に対応する
                - 次回の通話を楽しみにしてもらえるよう、温かい雰囲気で会話を終える""",
                "modalities": ["audio", "text"],
                "temperature": 0.8,
                "tool_choice": "auto",
                "tools": [
                    {
                        "name": "request_haiku",
                        "type": "function",
                        "description": "俳句の作成を専門エージェントに依頼します",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "context": {
                                    "type": "string",
                                    "description": "俳句を詠むための文脈"
                                }
                            },
                            "required": ["context"],
                            "additionalProperties": False
                        }
                    },
                    {
                        "name": "search_events",
                        "type": "function",
                        "description": "高齢者におすすめのイベント概要を検索します",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "conversation_context": {
                                    "type": "string",
                                    "description": "これまでの会話の内容や興味のある分野"
                                },
                                "count": {
                                    "type": "integer",
                                    "description": "検索するイベント数（1-5件）",
                                    "minimum": 1,
                                    "maximum": 5,
                                    "default": 3
                                }
                            },
                            "required": ["conversation_context"],
                            "additionalProperties": False
                        }
                    },
                    {
                        "name": "get_event_details",
                        "type": "function",
                        "description": "保存されたイベントの詳細情報を取得します（番号指定または曖昧な表現で検索可能）",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "selection": {
                                    "type": "string",
                                    "description": "イベントを選択する表現（例：「1番」「健康」「体操」「最初のやつ」「運動系」など）"
                                }
                            },
                            "required": ["selection"],
                            "additionalProperties": False
                        }
                    }
                ]
            }
        }
        await self.openai_ws.send(json.dumps(session_config))

    async def process_audio(self, audio_data: str) -> Optional[str]:
        """音声データを処理してOpenAIに送信"""
        if not self.openai_ws or self.openai_ws.state == State.CLOSED:
            await self.connect_to_openai()

        # セッション準備完了まで待機
        wait_count = 0
        while not self.session_ready and wait_count < 50:  # 最大5秒待機
            await asyncio.sleep(0.1)
            wait_count += 1

        if not self.session_ready:
            self.logger.warning("Session not ready, proceeding anyway")

        # 音声データをOpenAIに送信
        audio_append = {
            "type": "input_audio_buffer.append",
            "audio": audio_data
        }
        await self.openai_ws.send(json.dumps(audio_append))

        return None

    async def get_openai_response(self) -> Optional[Dict[str, Any]]:
        """OpenAIからのレスポンスを取得し、必要なServerEventのみ返す"""
        if self.openai_ws and self.openai_ws.state != State.CLOSED:
            try:
                message = await asyncio.wait_for(self.openai_ws.recv(), timeout=0.1)
                parsed_message = json.loads(message)

                # OpenAIイベントを内部処理
                server_event = await self._process_openai_event(parsed_message)
                return server_event
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                self.logger.error(
                    f"Error receiving from OpenAI: {e}", exc_info=True)
                return None
        return None

    async def _handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """ツール呼び出しの処理"""
        if function_name == "request_haiku":
            # 俳句エージェントに処理を委譲
            haiku_result = await self.haiku_agent.process(arguments)

            if haiku_result["success"]:
                # function call結果を送信
                function_output = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": arguments.get("call_id"),
                        "output": haiku_result["haiku"]
                    }
                }
                await self.openai_ws.send(json.dumps(function_output))

                # 新しいレスポンスを生成（音声を含む）
                await self.openai_ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"]
                    }
                }))

            return haiku_result

        elif function_name == "search_events":
            # イベント検索エージェントに処理を委譲
            if not self.user:
                error_message = "ユーザー情報が設定されていないため、イベントを検索できません"
                function_output = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": arguments.get("call_id"),
                        "output": error_message
                    }
                }
                await self.openai_ws.send(json.dumps(function_output))

                await self.openai_ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"]
                    }
                }))

                return {"success": False, "error": error_message}

            # EventAgentに渡すためのデータを準備
            event_input = {
                "user": self.user.model_dump(),
                "conversation": arguments.get("conversation_context", ""),
                "count": arguments.get("count", 3)
            }

            event_result = await self.event_agent.process(event_input)

            if event_result["success"] and event_result["events"]:
                # イベント情報をメモリに保存
                self.stored_events = event_result["events"]

                # 概要のみを番号付きで返す
                if len(self.stored_events) > 0:
                    events_text = "そういえば、今度いくつかイベントがあるそうですよ。"
                    for i, event_info in enumerate(self.stored_events, 1):
                        event_title = event_info["event"]["title"]
                        events_text += f"\n{i}番目は「{event_title}」"

                    events_text += "\n\n何番のイベントについて詳しく聞きたいですか？それとも全部は大丈夫ですか？"
                else:
                    events_text = "申し訳ございませんが、今週は特にお知らせするイベントがないようです。"
            else:
                events_text = event_result.get(
                    "message", "申し訳ございませんが、今週は特にお知らせするイベントがないようです。")

            # function call結果を送信
            function_output = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": arguments.get("call_id"),
                    "output": events_text
                }
            }
            await self.openai_ws.send(json.dumps(function_output))

            # 新しいレスポンスを生成（音声を含む）
            await self.openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"]
                }
            }))

            return event_result

        elif function_name == "get_event_details":
            # 保存されたイベントから柔軟に詳細を取得
            selection = arguments.get("selection", "")
            target_event = None

            # EventSelectorAgentを使って曖昧な表現を解決
            if self.stored_events:
                # イベント選択のためのプロンプトを作成
                selection_input = {
                    "user": self.user.model_dump() if self.user else {},
                    "conversation": f"ユーザーが「{selection}」について詳しく聞きたがっている",
                    "events": [event_info["event"] for event_info in self.stored_events],
                    "count": 1  # 1つだけ選択
                }

                selection_result = await self.event_selector_agent.process(selection_input)

                if selection_result["success"] and selection_result["selected_events"]:
                    # 最適なイベントを選択
                    selected_event_data = selection_result["selected_events"][0]["event"]
                    # stored_eventsから対応するものを見つける
                    for event_info in self.stored_events:
                        if event_info["event"]["event_id"] == selected_event_data["event_id"]:
                            target_event = event_info
                            break
                else:
                    # EventSelectorAgentが失敗した場合、番号による直接選択を試行
                    try:
                        # 数字を抽出して番号選択を試行
                        import re
                        numbers = re.findall(r'\d+', selection)
                        if numbers:
                            event_number = int(numbers[0])
                            if 1 <= event_number <= len(self.stored_events):
                                target_event = self.stored_events[event_number - 1]
                    except:
                        pass

            if target_event:
                event = target_event["event"]
                reason = target_event["reason"]

                # 日時をより自然な形式に変換
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(event['start_datetime'])
                    weekdays = ['月', '火', '水', '木', '金', '土', '日']
                    weekday = weekdays[dt.weekday()]
                    date_str = f"{dt.month}月{dt.day}日の{weekday}曜日、{'午前' if dt.hour < 12 else '午後'}{dt.hour if dt.hour <= 12 else dt.hour - 12}時"
                    if dt.minute > 0:
                        date_str += f"{dt.minute}分"
                except:
                    date_str = event['start_datetime']

                events_text = f"「{event['title']}」は、{date_str}から"
                events_text += f"{event['address_block']}で開催されます。"
                if event['description']:
                    events_text += f"\n{event['description']}"
                events_text += f"\n\nお問い合わせは、{event['contact_phone']}までお電話ください。"
                events_text += "よろしければ、参加を検討してみてくださいね。"
            else:
                events_text = f"申し訳ございませんが、「{selection}」に該当するイベントが見つかりませんでした。"
                if self.stored_events:
                    events_text += "もう一度、番号で指定していただくか、別の表現でお聞かせください。"

            # function call結果を送信
            function_output = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": arguments.get("call_id"),
                    "output": events_text
                }
            }
            await self.openai_ws.send(json.dumps(function_output))

            # 新しいレスポンスを生成（音声を含む）
            await self.openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"]
                }
            }))

            return {"success": True, "details": events_text}

        return {"success": False, "error": "Unknown function"}

    async def _process_openai_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """OpenAIイベントを処理してServerEventを返す"""
        event_type = event.get("type", "unknown")

        # Basic event type logging
        extra_info = {
            "event_type": event_type
        }

        # Log events and handle internal state
        if event_type == OpenAIEventType.ERROR:
            error = event.get("error", {})
            extra_info["error_details"] = error
            error_message = error.get("message", "Unknown error")
            error_code = error.get("code", "NO_CODE")
            self.logger.error(
                f"openai.error [{error_code}]: {error_message}", extra=extra_info)

            return {
                "type": ServerEventType.ERROR,
                "error": error_message
            }

        elif event_type == OpenAIEventType.SESSION_CREATED:
            self.session_ready = True
            self.logger.info("openai.session_ready", extra=extra_info)

            return {
                "type": ServerEventType.SESSION_CREATED,
                "session_id": event.get('session', {}).get('id', '')
            }

        elif event_type == OpenAIEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
            user_transcript = event.get("transcript", "")
            # TODO 話者の文字起こし完了.録音機能で実装

        elif event_type == OpenAIEventType.RESPONSE_DONE:
            # Reset last_assistant_item when response is complete
            self.last_assistant_item = None
            return {
                "type": ServerEventType.RESPONSE_DONE
            }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_DELTA:
            delta = event.get("delta", "")
            if delta:
                audio_chunk = base64.b64decode(delta)
                self.accumulated_audio.extend(audio_chunk)

                # Track last assistant item for interruption handling
                item_id = event.get('item_id')
                if item_id:
                    self.last_assistant_item = item_id

                return {
                    "type": ServerEventType.AUDIO,
                    "audio": delta,
                    "format": "g711_ulaw",
                    "item_id": item_id
                }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_DONE:
            if len(self.accumulated_audio) > 0:
                self.accumulated_audio = bytearray()

            return {
                "type": ServerEventType.CONTROL_AUDIO_DONE
            }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
            # TODO 録音機能で実装
            ai_transcript_delta = event.get("delta", "")

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE:
            # TODO 録音機能で実装
            transcript = event.get("transcript", "")

            if transcript:
                return {
                    "type": ServerEventType.TRANSCRIPT,
                    "transcript": transcript
                }

        elif event_type == OpenAIEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
            # Handle speech started event for interruption
            return {
                "type": ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED,
                "last_assistant_item": self.last_assistant_item
            }

        elif event_type == OpenAIEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA:
            # TODO 録音機能で実装
            transcript_delta = event.get("delta", "")

        elif event_type == OpenAIEventType.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE:
            function_name = event.get('name')
            arguments = json.loads(event.get('arguments', '{}'))
            arguments['call_id'] = event.get('call_id')
            # バックグラウンドで関数を実行
            # TODO toolsを呼ぶ前にrealtime apiに一言入れさせる
            asyncio.create_task(
                self._handle_function_call(function_name, arguments))

            return {
                "type": ServerEventType.AGENT_THINKING,
                "message": "考え中です",
                "function_name": function_name,
                "arguments": arguments
            }

        return None

    async def handle_interruption(self, audio_end_ms: int) -> None:
        """Handle interruption by truncating the current response"""
        if self.last_assistant_item and self.openai_ws:
            self.logger.info(
                f"Truncating item {self.last_assistant_item} at {audio_end_ms}ms")
            truncate_event = {
                "type": "conversation.item.truncate",
                "item_id": self.last_assistant_item,
                "content_index": 0,
                "audio_end_ms": audio_end_ms
            }
            await self.openai_ws.send(json.dumps(truncate_event))
            self.last_assistant_item = None

    async def start_conversation(self, user_id: Optional[str] = None):
        """会話を開始（ユーザー情報を設定してセッションを更新）"""
        if user_id:
            self.user_id = user_id
            # ユーザー情報を取得
            self.user = await self.user_repository.get_user_by_id(user_id)
            if self.user:
                self.logger.info(f"User data loaded for user_id: {user_id}")
                # ユーザー情報を含むinstructionsの差分更新
                await self._update_user_context()
            else:
                self.logger.warning(f"User not found for user_id: {user_id}")

    async def _update_user_context(self):
        """ユーザー情報を含むinstructionsの差分更新"""
        if not self.user:
            return

        from datetime import date
        # 年齢を計算
        age = None
        if self.user.birth_date:
            today = date.today()
            age = today.year - self.user.birth_date.year
            if (today.month, today.day) < (self.user.birth_date.month, self.user.birth_date.day):
                age -= 1

        user_context = f"""
        【ユーザー情報】
        - お名前: {self.user.last_name} {self.user.first_name}様
        - 年齢: {age}歳
        - 性別: {'男性' if self.user.gender.value == 'male' else '女性'}
        - 居住地: {self.user.prefecture}
        
        この情報を踏まえて、より親身で適切な対応を心がけてください。
        挨拶では「こんにちは、{self.user.last_name}さん。見守りのご連絡でお電話しました。今日もお元気でいらっしゃいますか？」から始めてください。
        """

        # instructionsの差分更新のみ
        session_update = {
            "type": "session.update",
            "session": {
                "instructions": f"""あなたは高齢者の見守りサービスの通話エージェントです。

                【目的】
                - 高齢者の異常や困りごとに気づくこと
                - 高齢者が孤立しないよう、会話を通じた心のケアを行うこと
                - 自治体が提供するイベント情報を、無理なく案内すること

                【会話スタイル】
                - 詰問や説教口調は避け、あたたかく丁寧な言葉づかいを使うこと
                - 会話は一方的にならないよう、相手の返答を想定して区切ること
                - 内容が機械的すぎたり、無感情にならないよう配慮すること
                - 「〜ですね」「〜ですか？」など、親しみやすい敬語を使うこと

                【会話の流れ（目安）】
                1. あいさつと健康状態の確認
                   - 体調や天候について軽く触れる
                
                2. 食事や生活の様子の話題
                   - 食事内容や食欲について尋ねる
                   - 水分補給や室温管理など、季節に応じた健康管理について話す
                
                3. ご近所や家族との交流確認
                   - 最近の家族やご近所との交流について尋ねる
                   - 孤立していないか、寂しさを感じていないか確認する
                
                4. 直近の地域イベントの案内
                   - 会話の流れで自然にイベント情報を提供する
                   - search_events関数を使って適切なイベントを紹介する
                   - 無理強いせず、「よろしければ」という表現を使う
                
                5. しめくくりと次回予告
                   - 「またお話できるのを楽しみにしていますね」
                   - 「どうかご自愛ください」
                   - 相手が心配事を口にした場合は、適切に対応する

                {user_context}

                【ツール使用ルール】
                - 俳句をリクエストされた場合は、request_haiku関数を呼び出す
                - イベント案内の段階で、search_events関数を呼び出してイベント概要を取得する
                - ユーザーが特定のイベントに興味を示したら、get_event_details関数で番号や曖昧な表現で詳細を取得する
                - ツール呼び出し前に「少々お待ちください」など一言添える

                【重要な注意事項】
                - 相手の発言に異常（体調不良、生活の困難、精神的な不安など）を感じたら、優先的に対応する
                - 長時間話を聞いてほしそうな場合は、丁寧に対応する
                - 次回の通話を楽しみにしてもらえるよう、温かい雰囲気で会話を終える"""
            }
        }
        await self.openai_ws.send(json.dumps(session_update))

    async def close(self):
        """接続をクローズ"""
        if self.openai_ws and self.openai_ws.state != State.CLOSED:
            await self.openai_ws.close()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """エージェントの処理を実行（基底クラスの実装）"""
        # この実装は主にWebSocketコントローラーから直接メソッドを呼ぶため、
        # ここでは簡単な実装のみ
        return {
            "success": True,
            "agent": self.name,
            "message": "Call agent is ready for WebSocket communication"
        }
