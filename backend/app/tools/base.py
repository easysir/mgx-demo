from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    output: Any = None
    error: str = None
    execution_time: float = 0.0


class Tool(ABC):
    """
    工具基类,所有工具都需要继承此类
    """
    
    def __init__(self):
        self.tool_name = self.__class__.__name__
        self.description = self.__doc__ or "No description available"
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具的主要方法
        
        Args:
            params: 工具执行所需的参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证参数是否有效
        
        Args:
            params: 待验证的参数
            
        Returns:
            bool: 参数是否有效
        """
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的参数schema
        
        Returns:
            Dict: 工具参数的JSON Schema
        """
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": {}
        }