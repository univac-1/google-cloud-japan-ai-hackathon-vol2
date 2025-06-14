from enum import Enum

class OpenAIEventType(str, Enum):
    ERROR = "error"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"
    SESSION_CREATED = "session.created"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
    INPUT_AUDIO_BUFFER_COMMITTED = "input_audio_buffer.committed"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED = "conversation.item.input_audio_transcription.completed"
    RESPONSE_DONE = "response.done"
    RESPONSE_CREATED = "response.created"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA = "conversation.item.input_audio_transcription.delta"