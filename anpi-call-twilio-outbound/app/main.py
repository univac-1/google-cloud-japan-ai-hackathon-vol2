import os
import sys
import json
import base64
import asyncio
import argparse
import re
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
import uvicorn
import logging
from pydantic import BaseModel
from agents.call_agent import CallAgent
from models.server_event_types import ServerEventType

# ログ設定 - デバッグレベルに変更
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
raw_domain = os.getenv('DOMAIN', '')
DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain)
PORT = int(os.getenv('PORT', 8080))


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = FastAPI()

# システムメッセージ
SYSTEM_MESSAGE = """
あなたは親切でフレンドリーなAIアシスタントです。日本語で自然に会話してください。
通話を通じて、相手の話を親身に聞き、適切な応答を心がけてください。
短く、分かりやすい返答を心がけてください。
初回の挨拶では、「こんにちは、AIアシスタントです。お話をお聞きします。」から始めてください。
"""

VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False

if not OPENAI_API_KEY:
    raise ValueError(
        'Missing the OpenAI API key. Please set it in the .env file.')


class OutboundCallRequest(BaseModel):
    to_number: str
    message: str = None
    user_id: str = None


@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Outbound Call Server is running!"}


@app.post("/outbound-call")
async def outbound_call_endpoint(request: OutboundCallRequest, http_request: Request):
    """API endpoint to initiate outbound calls"""
    try:
        user_id = request.user_id
        # DOMAINが設定されている場合はそちらを優先、なければリクエストホストを使用
        if DOMAIN:
            host = DOMAIN
            logger.info(f"Using DOMAIN from env: {host}")
        else:
            host = str(http_request.url.hostname)
            if http_request.url.port:
                host = f"{host}:{http_request.url.port}"
            logger.info(f"Using request host: {host}")

        logger.info(f"Making outbound call to {request.to_number}")

        # user_idは個別にパラメータとして渡さず、TwiMLのConnectでカスタムパラメータとして渡す

        # TwiMLでuser_idをカスタムパラメータとして含める
        stream_element = f'<Stream url="wss://{host}/media-stream"'
        if user_id:
            stream_element += f'><Parameter name="user_id" value="{user_id}" /></Stream>'
        else:
            stream_element += ' />'

        call = client.calls.create(
            twiml=f'''<Response>
                <Pause length="1"/>
                <Connect>
                    {stream_element}
                </Connect>
            </Response>''',
            to=request.to_number,
            from_=PHONE_NUMBER_FROM
        )

        logger.info(f"Call initiated with SID: {call.sid}")
        logger.info(f"WebSocket URL: wss://{host}/media-stream")
        if user_id:
            logger.info(f"Using user_id: {user_id}")

        return {
            "success": True,
            "call_sid": call.sid,
            "to_number": request.to_number,
            "message": "Call initiated successfully",
            "websocket_url": f"wss://{host}/media-stream",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error making outbound call: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    logger.info("WebSocket client connecting...")

    await websocket.accept()
    logger.info("WebSocket client connected successfully")

    # Connection specific state
    stream_sid = None
    latest_media_timestamp = 0
    mark_queue = []
    response_start_timestamp_twilio = None
    last_assistant_item = None
    is_running = True

    # Create CallAgent instance - user_idは後でstartイベントで設定
    call_agent = CallAgent()

    # OpenAIに事前接続
    await call_agent.connect_to_openai()
    logger.info("CallAgent connected to OpenAI successfully")

    async def receive_from_twilio():
        """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
        nonlocal stream_sid, latest_media_timestamp, is_running
        try:
            async for message in websocket.iter_text():
                data = json.loads(message)
                logger.debug(f"Received from Twilio: {data['event']}")

                if data['event'] == 'media':
                    latest_media_timestamp = int(
                        data['media']['timestamp'])
                    # Send audio to CallAgent
                    try:
                        await call_agent.process_audio(data['media']['payload'])
                    except Exception as e:
                        logger.error(f"Error sending audio to CallAgent: {e}")
                        break

                elif data['event'] == 'start':
                    stream_sid = data['start']['streamSid']
                    logger.info(
                        f"Incoming stream has started {stream_sid}")
                    response_start_timestamp_twilio = None
                    latest_media_timestamp = 0

                    user_id = None

                    # TwiMLのカスタムパラメータからuser_idを取得
                    if 'customParameters' in data['start']:
                        custom_params = data['start']['customParameters']
                        logger.info(f"Custom parameters: {custom_params}")
                        if 'user_id' in custom_params:
                            user_id = custom_params['user_id']
                            logger.info(
                                f"Found user_id in custom parameters: {user_id}")

                    # 会話を開始（ユーザー情報設定と反映）
                    await call_agent.start_conversation(user_id)

                elif data['event'] == 'stop':
                    logger.info(
                        f"Received stop event from Twilio - user hung up")
                    is_running = False
                    break

                elif data['event'] == 'mark':
                    if mark_queue:
                        mark_queue.pop(0)

        except WebSocketDisconnect:
            logger.info("Twilio WebSocket client disconnected.")
            is_running = False
        except Exception as e:
            logger.error(f"Error in receive_from_twilio: {e}")
            is_running = False

    async def send_to_twilio():
        """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
        nonlocal stream_sid, response_start_timestamp_twilio, is_running
        try:
            while is_running:
                # Get response from CallAgent
                response = await call_agent.get_openai_response()
                if response is None:
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.01)
                    continue

                event_type = response.get('type')

                if event_type == ServerEventType.AUDIO:
                    # Audio is already base64 encoded from CallAgent
                    audio_delta = {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": response['audio']
                        }
                    }
                    await websocket.send_json(audio_delta)

                    if response_start_timestamp_twilio is None:
                        response_start_timestamp_twilio = latest_media_timestamp

                    # Track last assistant item from response
                    item_id = response.get('item_id')
                    if item_id:
                        last_assistant_item = item_id

                    await send_mark(websocket, stream_sid)

                # Handle speech started event from CallAgent
                elif event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                    # Get last_assistant_item from response if available
                    item_from_response = response.get('last_assistant_item')
                    if item_from_response:
                        last_assistant_item = item_from_response
                    await handle_speech_started_event()

        except Exception as e:
            logger.error(f"Error in send_to_twilio: {e}")

    async def handle_speech_started_event():
        """Handle interruption when the caller's speech starts."""
        nonlocal response_start_timestamp_twilio, last_assistant_item
        logger.info("Handling speech started event.")

        # Calculate elapsed time and send truncate event to OpenAI
        if mark_queue and response_start_timestamp_twilio is not None and last_assistant_item:
            elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
            logger.info(
                f"Interrupting response. Elapsed time: {elapsed_time}ms, Item ID: {last_assistant_item}")

            # Send truncate event through CallAgent
            await call_agent.handle_interruption(elapsed_time)

        # Clear Twilio audio buffer
        await websocket.send_json({
            "event": "clear",
            "streamSid": stream_sid
        })

        mark_queue.clear()
        response_start_timestamp_twilio = None
        last_assistant_item = None

    async def send_mark(connection, stream_sid):
        if stream_sid:
            mark_event = {
                "event": "mark",
                "streamSid": stream_sid,
                "mark": {"name": "responsePart"}
            }
            await connection.send_json(mark_event)
            mark_queue.append('responsePart')

    try:
        await asyncio.gather(receive_from_twilio(), send_to_twilio())
    except Exception as e:
        logger.error(f"Error in WebSocket communication: {e}")
    finally:
        logger.info("WebSocket session ended")
        await call_agent.close()


# These functions are now handled internally by CallAgent


async def check_number_allowed(to: str) -> bool:
    """発信許可番号かどうかチェック"""
    try:
        # Twilio Dev Phoneや検証済み発信元をチェック
        incoming = client.incoming_phone_numbers.list(phone_number=to)
        outgoing = client.outgoing_caller_ids.list(phone_number=to)
        return bool(incoming or outgoing)
    except Exception as e:
        logger.error(f"Error checking number permission: {e}")
        return False


async def make_call(to: str, user_id: str = None):
    """アウトバウンドコールを実行"""
    if not await check_number_allowed(to):
        raise ValueError(
            f"{to} は発信許可がありません。Twilio Dev PhoneまたはVerified Caller IDsに登録してください。")

    # TwiMLでMedia Streamを設定
    stream_element = f'<Stream url="wss://{DOMAIN}/media-stream"'
    if user_id:
        stream_element += f'><Parameter name="user_id" value="{user_id}" /></Stream>'
    else:
        stream_element += ' />'

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Connect>{stream_element}</Connect>'
        '</Response>'
    )

    try:
        call = client.calls.create(
            from_=PHONE_NUMBER_FROM,
            to=to,
            twiml=twiml
        )
        logger.info(f"Call started with SID: {call.sid}")
        print(f"✅ Call started successfully!")
        print(f"   Call SID: {call.sid}")
        print(f"   From: {PHONE_NUMBER_FROM}")
        print(f"   To: {to}")
        print(f"   Stream URL: wss://{DOMAIN}/media-stream")
        if user_id:
            print(f"   User ID: {user_id}")

    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Twilio Outbound Call with OpenAI Realtime API")
    parser.add_argument('--call', help="呼び出す番号をE.164形式で指定 (例: +8190xxxxxxxx)")
    parser.add_argument('--server-only', action='store_true',
                        help="サーバーのみを起動（発信は行わない）")
    parser.add_argument('--user-id', help="通話で使用するユーザーID（動作確認用）")
    args = parser.parse_args()
    # server-onlyでない場合は--callが必須
    if not args.server_only and not args.call:
        print("❌ --call オプションが必要です")
        print("   例: python main.py --call=+8190xxxxxxxx")
        print("   または: python main.py --server-only")
        print("   ユーザー指定: python main.py --call=+8190xxxxxxxx --user-id=user123")
        exit(1)

    # 設定確認
    print("🔧 設定確認:")
    print(
        f"   TWILIO_ACCOUNT_SID: {'✅ 設定済み' if TWILIO_ACCOUNT_SID else '❌ 未設定'}")
    print(
        f"   TWILIO_AUTH_TOKEN: {'✅ 設定済み' if TWILIO_AUTH_TOKEN else '❌ 未設定'}")
    print(f"   PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM or '❌ 未設定'}")
    print(f"   OPENAI_API_KEY: {'✅ 設定済み' if OPENAI_API_KEY else '❌ 未設定'}")
    print(f"   DOMAIN: {DOMAIN or '❌ 未設定'}")
    print(f"   PORT: {PORT}")
    if args.user_id:
        print(f"   USER_ID: {args.user_id}")
    print()

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, PHONE_NUMBER_FROM, OPENAI_API_KEY, DOMAIN]):
        print("❌ 必要な環境変数が設定されていません。.envファイルを確認してください。")
        exit(1)

    try:
        # 発信処理（server-onlyオプションでない場合のみ）
        if not args.server_only:
            print(f"📞 発信を開始します: {args.call}")
            asyncio.run(make_call(args.call, args.user_id))
            print("✅ 発信が完了しました")

        # サーバー起動
        print("🚀 サーバーを起動します...")
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except KeyboardInterrupt:
        print("\n👋 サーバーを停止しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        exit(1)
