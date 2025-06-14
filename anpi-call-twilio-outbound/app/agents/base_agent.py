from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """基底エージェントクラス"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """エージェントの処理を実行"""
        pass