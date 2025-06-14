from enum import Enum

class ClientEventType(str, Enum):
    AUDIO = "audio"
    CONTROL = "control"
    CONTROL_END_CONVERSATION = "control_end_conversation"
    USER_INFO = "user_info"