from typing import Dict, Any, List
from app.tools.base import Tool, ToolResult


class ToolExecutor:
    """
    工具执行器,负责管理和执行工具
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_tool(self, tool: Tool):
        """
        注册工具
        
        Args:
            tool: 要注册的工具实例
        """
        self.tools[tool.tool_name] = tool
        print(f"Tool registered: {tool.tool_name}")
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}"
            )
        
        tool = self.tools[tool_name]
        
        # 验证参数
        if not tool.validate_params(params):
            return ToolResult(
                success=False,
                error=f"Invalid parameters for tool: {tool_name}"
            )
        
        # 执行工具
        result = await tool.execute(params)
        
        # 记录执行历史
        self.execution_history.append({
            "tool_name": tool_name,
            "params": params,
            "result": result.dict(),
            "timestamp": None  # 可以添加时间戳
        })
        
        return result
    
    def get_available_tools(self) -> List[str]:
        """
        获取所有可用工具的列表
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self.tools.keys())
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        获取工具的schema
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Dict: 工具的schema
        """
        if tool_name not in self.tools:
            return {}
        
        return self.tools[tool_name].get_schema()