from enum import Enum


class ServerEventType(str, Enum):
    """サーバーからクライアントに送信するイベントタイプ"""
    
    # 音声関連
    AUDIO = "response.audio.delta"
    AUDIO_DONE = "response.audio.done"
    CONTROL_AUDIO_DONE = "control.audio.done"
    
    # テキスト関連
    TRANSCRIPT = "response.transcript"
    
    # セッション関連
    SESSION_CREATED = "session.created"
    CONTROL_SESSION_CREATED = "control.session.created"
    
    # レスポンス関連
    RESPONSE_DONE = "response.done"
    
    # 制御関連
    CONTROL_CONVERSATION_ENDED = "control.conversation.ended"
    AGENT_THINKING = "agent.thinking"
    
    # エラー
    ERROR = "error"
