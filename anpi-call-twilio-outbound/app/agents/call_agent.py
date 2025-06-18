import os
import json
import base64
import asyncio
import logging
from datetime import date
from typing import Dict, Any, Optional
import websockets
from websockets.protocol import State
from agents.event_agent import EventAgent
from models.openai_event_types import OpenAIEventType
from models.server_event_types import ServerEventType
from repositories.cloudsql_user_repository import CloudSQLUserRepository
from models.schemas import User


logger = logging.getLogger(__name__)


class CallAgent:
    """通話エージェント - OpenAI Realtime APIを使用"""

    # インストラクション生成用メソッド
    def _generate_instructions(self) -> str:
        """共通のインストラクションを生成"""
        greeting = "「こんにちは。見守りのご連絡でお電話しました。今日もお元気でいらっしゃいますか？」から始める"
        user_context = ""

        if self.user:
            greeting = f"「こんにちは、{self.user.last_name}さん。見守りのご連絡でお電話しました。今日もお元気でいらっしゃいますか？」から始める"

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
        """

        return f"""あなたは高齢者の見守りサービスの通話エージェントです。

                【目的】
                - 高齢者の異常や困りごとに気づくこと
                - 高齢者が孤立しないよう、会話を通じた心のケアを行うこと
                - 自治体が提供するイベント情報を、無理なく案内すること

                【会話スタイル】
                - 詰問や説教口調は避け、あたたかく丁寧な言葉づかいを使うこと
                - 会話は一方的にならないよう、相手の返答を想定して区切ること
                - 内容が機械的すぎたり、無感情にならないよう配慮すること

                【会話の流れ（目安）】
                1. あいさつと健康状態の確認
                   - {greeting}
                   - 体調や天候について軽く触れる
                
                2. 食事や生活の様子の話題
                   - 食事内容や食欲について尋ねる
                   - 水分補給や室温管理など、季節に応じた健康管理について話す
                
                3. ご近所や家族との交流確認
                   - 最近の家族やご近所との交流について尋ねる
                   - 孤立していないか、寂しさを感じていないか確認する
                
                4. 直近の地域イベントの案内
                   - 会話の流れで自然にイベント情報を提供する
                   - search_events関数を使って適切なイベントを検索する
                   - イベント紹介で相手を退屈させないように、ユーザーが興味を示したときだけ、会話履歴から詳細内容を説明する
                
                5. しめくくり
                   - 会話をユーモアを交えてまとめて、通話を終わりにする挨拶でしめる

                {user_context}

                【ツール使用ルール】
                - イベントを探すときは、search_events関数でイベント情報を検索する
                - ツール呼び出し前に「少々お待ちください」など一言添える""",

    def __init__(self):
        self.name = "通話エージェント"
        self.user_id = None
        # CloudSQLUserRepositoryを使用
        self.user_repository = CloudSQLUserRepository()
        self.user: Optional[User] = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_ws: Optional[Any] = None
        self.event_agent = EventAgent()
        self.conversation_history = []
        self.accumulated_audio = bytearray()
        self.session_ready = False
        self.last_assistant_item = None
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
                "instructions": self._generate_instructions(),
                "modalities": ["audio", "text"],
                "temperature": 0.8,
                "tool_choice": "auto",
                "tools": [
                    {
                        "name": "search_events",
                        "type": "function",
                        "description": "高齢者におすすめのイベント情報を検索し、会話コンテキストに追加します",
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
        if function_name == "search_events":
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
                # イベント情報をシンプルなJSON形式に整形
                events_json = []
                for event_info in event_result["events"]:
                    event = event_info["event"]
                    events_json.append({
                        "タイトル": event['title'],
                        "日時": event['start_datetime'],
                        "場所": event['address_block'],
                        "内容": event['description'],
                        "電話": event['contact_phone']
                    })

                context_message = f"おすすめイベント: {json.dumps(events_json, ensure_ascii=False)}"

                # function call結果を送信（会話履歴に追加）
                function_output = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": arguments.get("call_id"),
                        "output": context_message
                    }
                }
                await self.openai_ws.send(json.dumps(function_output))

                # AIに自然な形でイベントを紹介するよう指示
                await self.openai_ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"],
                        "instructions": "調査したイベント情報を踏まえて、調査の概要を簡潔に紹介してください。相手が興味を示したときだけ詳細を説明してください。"
                    }
                }))
            else:
                # イベントが見つからない場合
                function_output = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": arguments.get("call_id"),
                        "output": "現在、お住まいの地域で開催予定のイベントが見つかりませんでした。"
                    }
                }
                await self.openai_ws.send(json.dumps(function_output))

                await self.openai_ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"]
                    }
                }))

            return event_result

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

        # instructionsの差分更新のみ
        session_update = {
            "type": "session.update",
            "session": {
                "instructions": self._generate_instructions()
            }
        }
        await self.openai_ws.send(json.dumps(session_update))

    async def close(self):
        """接続をクローズ"""
        if self.openai_ws and self.openai_ws.state != State.CLOSED:
            await self.openai_ws.close()
