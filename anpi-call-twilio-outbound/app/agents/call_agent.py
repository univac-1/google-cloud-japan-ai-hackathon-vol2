import os
import json
import base64
import asyncio
import logging
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.agents.haiku_agent import HaikuAgent
from app.agents.event_agent import EventAgent
from app.models.openai_event_types import OpenAIEventType
from app.models.server_event_types import ServerEventType
from app.repositories.cloudsql_user_repository import CloudSQLUserRepository
from app.models.schemas import User

try:
    import websockets
except ImportError:
    websockets = None


class CallAgent(BaseAgent):
    """通話エージェント - OpenAI Realtime APIを使用"""

    def __init__(self, client_id: str, user_id: Optional[str] = None):
        super().__init__("通話エージェント")
        self.client_id = client_id
        self.user_id = user_id
        # CloudSQLUserRepositoryを使用
        self.user_repository = CloudSQLUserRepository()
        self.user: Optional[User] = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_ws: Optional[Any] = None
        self.haiku_agent = HaikuAgent()
        self.event_agent = EventAgent()
        self.conversation_history = []
        self.accumulated_audio = bytearray()
        self.session_ready = False
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}")

    async def connect_to_openai(self):
        """OpenAI Realtime APIに接続"""
        if not websockets:
            raise RuntimeError("websockets library not available")

        # ユーザー情報を取得
        if self.user_id and not self.user:
            self.user = await self.user_repository.get_user_by_id(self.user_id)
            if self.user:
                self.logger.info(
                    f"User data loaded for user_id: {self.user_id}")
            else:
                self.logger.warning(
                    f"User not found for user_id: {self.user_id}")

        if not self.openai_ws or self.openai_ws.closed:
            self.openai_ws = await websockets.connect(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                extra_headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
            )
            await self._initialize_session()

    async def _initialize_session(self):
        """OpenAIセッションの初期化"""
        # ユーザー情報を含めたinstructionsを構築
        user_context = ""
        if self.user:
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
                """

        session_config = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 2000
                },
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {"model": "whisper-1"},
                "voice": "alloy",
                "instructions": f"""あなたは高齢者の話し相手をする優しいAIアシスタントです。
                相手に寄り添い、相手を楽しませることを心がけてください。
                会話を終える際は、次の会話が楽しみになるような一言を添えて挨拶してください。
                {user_context}
                【ツール使用ルール】
                - 俳句をリクエストされた場合（「何か詠んで」「俳句を詠んで」「詩を聞かせて」「一句お願い」など）は、request_haiku関数を呼び出してください。
                - イベントについて聞かれた場合（「何かイベントはない？」「参加できる催し物は？」「どんな活動がある？」「おすすめのイベント」など）は、recommend_events関数を呼び出してください。
                - 該当する要求があった場合のみ適切な関数を呼び出し、それ以外は通常の会話を行ってください。""",
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
                        "name": "recommend_events",
                        "type": "function",
                        "description": "高齢者におすすめのイベントを提案します",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "conversation_context": {
                                    "type": "string",
                                    "description": "これまでの会話の内容や興味のある分野"
                                },
                                "count": {
                                    "type": "integer",
                                    "description": "提案するイベント数（1-5件）",
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
        if not self.openai_ws or self.openai_ws.closed:
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
        if self.openai_ws and not self.openai_ws.closed:
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

        elif function_name == "recommend_events":
            # イベント提案エージェントに処理を委譲
            if not self.user:
                error_message = "ユーザー情報が設定されていないため、イベントを提案できません"
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

            if event_result["success"]:
                # イベント結果を整形
                if event_result["events"]:
                    events_text = "おすすめのイベントをご紹介します：\n\n"
                    for i, event_info in enumerate(event_result["events"], 1):
                        event = event_info["event"]
                        reason = event_info["reason"]
                        events_text += f"{i}. {event['title']}\n"
                        events_text += f"   日時: {event['start_datetime']}\n"
                        events_text += f"   場所: {event['prefecture']}{event['address_block']}\n"
                        events_text += f"   内容: {event['description']}\n"
                        events_text += f"   おすすめ理由: {reason}\n"
                        events_text += f"   お問い合わせ: {event['contact_phone']}\n\n"
                else:
                    events_text = event_result.get(
                        "message", "申し訳ございませんが、現在おすすめできるイベントが見つかりませんでした。")

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

        return {"success": False, "error": "Unknown function"}

    async def _process_openai_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """OpenAIイベントを処理してServerEventを返す"""
        event_type = event.get("type", "unknown")

        # Basic event type logging
        extra_info = {
            "client_id": self.client_id,
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

        elif event_type == OpenAIEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
            self.logger.debug("openai.speech_started", extra=extra_info)

            return {
                "type": ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED
            }

        elif event_type == OpenAIEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
            self.logger.debug("openai.speech_stopped", extra=extra_info)

        elif event_type == OpenAIEventType.INPUT_AUDIO_BUFFER_COMMITTED:
            self.logger.debug("openai.buffer_committed", extra=extra_info)

        elif event_type == OpenAIEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
            user_transcript = event.get("transcript", "")
            self.logger.debug("user_speech_recognized", extra={
                "client_id": self.client_id,
                "user_said": user_transcript,
                "transcript_length": len(user_transcript) if user_transcript else 0
            })

        elif event_type == OpenAIEventType.RESPONSE_CREATED:
            self.logger.debug("ai_response_started", extra=extra_info)

        elif event_type == OpenAIEventType.RESPONSE_DONE:
            self.logger.debug("ai_response_completed", extra=extra_info)

            return {
                "type": ServerEventType.RESPONSE_DONE
            }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_DELTA:
            delta = event.get("delta", "")
            if delta:
                audio_chunk = base64.b64decode(delta)
                self.accumulated_audio.extend(audio_chunk)

                return {
                    "type": ServerEventType.AUDIO,
                    "audio": delta,
                    "format": "g711_ulaw"
                }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_DONE:
            if len(self.accumulated_audio) > 0:
                self.accumulated_audio = bytearray()

            return {
                "type": ServerEventType.CONTROL_AUDIO_DONE
            }

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
            ai_transcript_delta = event.get("delta", "")
            self.logger.debug(f"AI_TRANSCRIPT_DELTA: '{ai_transcript_delta}'", extra={
                "client_id": self.client_id,
                "delta": ai_transcript_delta
            })

        elif event_type == OpenAIEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE:
            transcript = event.get("transcript", "")
            self.logger.debug("ai_transcript_received", extra={
                "client_id": self.client_id,
                "transcript": transcript
            })

            if transcript:
                return {
                    "type": ServerEventType.TRANSCRIPT,
                    "transcript": transcript
                }

        elif event_type == OpenAIEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA:
            transcript_delta = event.get("delta", "")
            self.logger.debug(f"USER_TRANSCRIPT_DELTA: '{transcript_delta}'", extra={
                "client_id": self.client_id,
                "delta": transcript_delta
            })

        elif event_type == OpenAIEventType.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE:
            function_name = event.get('name')
            arguments = json.loads(event.get('arguments', '{}'))
            arguments['call_id'] = event.get('call_id')

            self.logger.debug("openai.function_call", extra={
                "client_id": self.client_id,
                "function_name": function_name,
                "arguments": arguments
            })

            # エージェント呼び出し通知とバックグラウンド実行
            if function_name == "request_haiku":
                # バックグラウンドで関数を実行
                asyncio.create_task(
                    self._handle_function_call(function_name, arguments))

                return {
                    "type": ServerEventType.AGENT_THINKING,
                    "message": "俳句エージェントが俳句を考えています...",
                    "function_name": function_name,
                    "arguments": arguments
                }

            elif function_name == "recommend_events":
                # バックグラウンドで関数を実行
                asyncio.create_task(
                    self._handle_function_call(function_name, arguments))

                return {
                    "type": ServerEventType.AGENT_THINKING,
                    "message": "おすすめのイベントを探しています...",
                    "function_name": function_name,
                    "arguments": arguments
                }

        else:
            # その他のイベントはログのみ
            self.logger.debug(f"openai.{event_type}", extra={
                **extra_info,
                "full_event": event
            })

        return None

    async def close(self):
        """接続をクローズ"""
        if self.openai_ws and not self.openai_ws.closed:
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
