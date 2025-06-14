import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.agents.call_agent import CallAgent
from app.models.schemas import ClientMessage
from app.models.server_event_types import ServerEventType
from app.models.client_event_types import ClientEventType
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.call_agents: Dict[str, CallAgent] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.call_agents[client_id] = CallAgent(client_id, user_id)
        await self.call_agents[client_id].connect_to_openai()
        logger.info(f"Client {client_id} connected with user_id: {user_id}")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.call_agents:
            await self.call_agents[client_id].close()
            del self.call_agents[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_message(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, user_id: str = Query(default=None)):
    await manager.connect(websocket, client_id, user_id)
    call_agent = manager.call_agents[client_id]

    try:
        # OpenAIからのレスポンスを処理する非同期タスク
        async def handle_openai_responses():
            while True:
                try:
                    server_event = await call_agent.get_openai_response()
                    if server_event is None:
                        continue

                    event_type = server_event.get("type")

                    # ServerEventタイプに応じてクライアントに送信
                    if event_type == ServerEventType.AUDIO:
                        await manager.send_message(server_event, client_id)
                        logger.debug("to_client.audio", extra={
                            "client_id": client_id,
                            "delta_length": len(server_event.get("audio", ""))
                        })

                    elif event_type == ServerEventType.CONTROL_AUDIO_DONE:
                        await manager.send_message(server_event, client_id)
                        logger.info("to_client.audio_done", extra={
                                    "client_id": client_id})

                    elif event_type == ServerEventType.ERROR:
                        await manager.send_message(server_event, client_id)
                        logger.error(f"to_client.error: {server_event.get('error')}", extra={
                            "client_id": client_id,
                            "error": server_event.get("error")
                        })

                    elif event_type == ServerEventType.SESSION_CREATED:
                        await manager.send_message(server_event, client_id)
                        logger.info("to_client.session_created",
                                    extra={"client_id": client_id})

                    elif event_type == ServerEventType.TRANSCRIPT:
                        await manager.send_message(server_event, client_id)
                        logger.info("to_client.ai_transcript", extra={
                            "client_id": client_id,
                            "transcript": server_event.get("transcript")
                        })

                    elif event_type == ServerEventType.RESPONSE_DONE:
                        await manager.send_message(server_event, client_id)
                        logger.info("to_client.response_done",
                                    extra={"client_id": client_id})

                    elif event_type == ServerEventType.AGENT_THINKING:
                        await manager.send_message(server_event, client_id)
                        logger.info("to_client.agent_thinking", extra={
                            "client_id": client_id,
                            "thinking_message": server_event.get("message")
                        })

                except Exception:
                    logger.error(
                        "Error handling OpenAI response", exc_info=True)
                    await asyncio.sleep(0.1)

        # OpenAIレスポンスハンドラーを起動
        response_task = asyncio.create_task(handle_openai_responses())

        # クライアントからのメッセージを処理
        while True:
            data = await websocket.receive_json()
            message = ClientMessage(**data)

            if message.type == ClientEventType.AUDIO:
                # 音声データをOpenAIに転送
                audio_data = message.data.get("audio_data", "")
                await call_agent.process_audio(audio_data)
                logger.debug("from_client.audio", extra={
                             "client_id": client_id})

            elif message.type == ClientEventType.CONTROL:
                # 制御メッセージ
                action = message.data.get("action", "")
                if action == "end_conversation":
                    logger.info("from_client.end_conversation",
                                extra={"client_id": client_id})

                    await manager.send_message({
                        "type": ServerEventType.CONTROL_CONVERSATION_ENDED,
                        "message": "また今度お話ししましょうね。楽しみにしています！"
                    }, client_id)
                    logger.info("to_client.conversation_ended",
                                extra={"client_id": client_id})
                    break

            elif message.type == ClientEventType.CONTROL_END_CONVERSATION:
                # 会話終了リクエスト（従来の形式）
                logger.info("from_client.end_conversation",
                            extra={"client_id": client_id})

                await manager.send_message({
                    "type": ServerEventType.CONTROL_CONVERSATION_ENDED,
                    "message": "また今度お話ししましょうね。楽しみにしています！"
                }, client_id)
                logger.info("to_client.conversation_ended",
                            extra={"client_id": client_id})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", extra={"client_id": client_id})
    except Exception as e:
        logger.error("Error in websocket connection", extra={
                     "client_id": client_id}, exc_info=True)
        await manager.send_message({
            "type": ServerEventType.ERROR,
            "error": str(e)
        }, client_id)
    finally:
        response_task.cancel()
        await manager.disconnect(client_id)
