import os, json, base64, asyncio, argparse, re
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
import websockets
from dotenv import load_dotenv
import uvicorn
import logging
from pydantic import BaseModel

# ログ設定 - デバッグレベルに変更
logging.basicConfig(
    level=logging.DEBUG,
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
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

class OutboundCallRequest(BaseModel):
    to_number: str
    message: str = None

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Outbound Call Server is running!"}

@app.post("/outbound-call")
async def outbound_call_endpoint(request: OutboundCallRequest, http_request: Request):
    """API endpoint to initiate outbound calls"""
    try:
        # Get the current request's host for webhook URL
        # Use the request host to build the WebSocket URL
        host = str(http_request.url.hostname)
        if http_request.url.port:
            host = f"{host}:{http_request.url.port}"
        
        logger.info(f"Making outbound call to {request.to_number}")
        logger.info(f"Using host: {host}")
        
        call = client.calls.create(
            twiml=f'''<Response>
                <Say voice="alice" language="ja-JP">こんにちは、AIアシスタントです。お話をお聞きします。</Say>
                <Pause length="1"/>
                <Connect>
                    <Stream url="wss://{host}/media-stream" />
                </Connect>
            </Response>''',
            to=request.to_number,
            from_=PHONE_NUMBER_FROM
        )
        
        logger.info(f"Call initiated with SID: {call.sid}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "to_number": request.to_number,
            "message": "Call initiated successfully"
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
    logger.info("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    logger.debug(f"Received from Twilio: {data['event']}")
                    
                    if data['event'] == 'media':
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        try:
                            await openai_ws.send(json.dumps(audio_append))
                        except Exception as e:
                            logger.error(f"Error sending audio to OpenAI: {e}")
                            break
                        
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        logger.info(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                        
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
                            
            except WebSocketDisconnect:
                logger.info("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        logger.info(f"Received event: {response['type']}")
                        logger.debug(f"Full response: {response}")

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                logger.debug(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        # Update last_assistant_item safely
                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        logger.info("Speech started detected.")
                        if last_assistant_item:
                            logger.info(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
                            
            except Exception as e:
                logger.error(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            logger.info("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    logger.debug(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        logger.debug(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "挨拶をしてください"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    logger.info('Sending session update')
    logger.debug(f'Session update: {json.dumps(session_update)}')
    await openai_ws.send(json.dumps(session_update))

    # AI が最初に話すようにする
    await send_initial_conversation_item(openai_ws)

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

async def make_call(to: str):
    """アウトバウンドコールを実行"""
    if not await check_number_allowed(to):
        raise ValueError(f"{to} は発信許可がありません。Twilio Dev PhoneまたはVerified Caller IDsに登録してください。")
    
    # TwiMLでMedia Streamを設定
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Say>OK, please go ahead.</Say>'
        f'<Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect>'
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
        
    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twilio Outbound Call with OpenAI Realtime API")
    parser.add_argument('--call', help="呼び出す番号をE.164形式で指定 (例: +8190xxxxxxxx)")
    parser.add_argument('--server-only', action='store_true', help="サーバーのみを起動（発信は行わない）")
    args = parser.parse_args()
    
    # server-onlyでない場合は--callが必須
    if not args.server_only and not args.call:
        print("❌ --call オプションが必要です")
        print("   例: python main.py --call=+8190xxxxxxxx")
        print("   または: python main.py --server-only")
        exit(1)
    
    # 設定確認
    print("🔧 設定確認:")
    print(f"   TWILIO_ACCOUNT_SID: {'✅ 設定済み' if TWILIO_ACCOUNT_SID else '❌ 未設定'}")
    print(f"   TWILIO_AUTH_TOKEN: {'✅ 設定済み' if TWILIO_AUTH_TOKEN else '❌ 未設定'}")
    print(f"   PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM or '❌ 未設定'}")
    print(f"   OPENAI_API_KEY: {'✅ 設定済み' if OPENAI_API_KEY else '❌ 未設定'}")
    print(f"   DOMAIN: {DOMAIN or '❌ 未設定'}")
    print(f"   PORT: {PORT}")
    print()
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, PHONE_NUMBER_FROM, OPENAI_API_KEY, DOMAIN]):
        print("❌ 必要な環境変数が設定されていません。.envファイルを確認してください。")
        exit(1)
    
    
    try:
        # 発信処理（server-onlyオプションでない場合のみ）
        if not args.server_only:
            print(f"📞 発信を開始します: {args.call}")
            asyncio.run(make_call(args.call))
            print("✅ 発信が完了しました")
        
        # サーバー起動
        print("🚀 サーバーを起動します...")
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except KeyboardInterrupt:
        print("\n👋 サーバーを停止しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        exit(1)
