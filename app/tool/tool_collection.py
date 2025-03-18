"""Collection classes for managing multiple tools."""
from typing import Any, Dict, List

from app.exceptions import ToolError
from app.tool.base import BaseTool, ToolFailure, ToolResult


class ToolCollection:
    """
    工具集合类：用于管理多个已定义工具
    
    提供工具的添加、获取、执行等功能。
    """

    def __init__(self, *tools: BaseTool):
        """
        初始化工具集合
        
        参数:
            *tools: 要添加的工具列表
        """
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}

    def __iter__(self):
        """
        使工具集合可迭代
        
        返回:
            iterator: 工具迭代器
        """
        return iter(self.tools)

    def to_params(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的参数定义
        
        返回:
            List[Dict[str, Any]]: 工具参数定义列表
        """
        return [tool.to_param() for tool in self.tools]

    async def execute(
        self, *, name: str, tool_input: Dict[str, Any] = None
    ) -> ToolResult:
        """
        执行指定名称的工具
        
        参数:
            name: 工具名称
            tool_input: 工具输入参数
            
        返回:
            ToolResult: 工具执行结果
        """
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            result = await tool(**tool_input)
            return result
        except ToolError as e:
            return ToolFailure(error=e.message)

    async def execute_all(self) -> List[ToolResult]:
        """
        按顺序执行集合中的所有工具
        
        返回:
            List[ToolResult]: 所有工具的执行结果列表
        """
        results = []
        for tool in self.tools:
            try:
                result = await tool()
                results.append(result)
            except ToolError as e:
                results.append(ToolFailure(error=e.message))
        return results

    def get_tool(self, name: str) -> BaseTool:
        """
        获取指定名称的工具
        
        参数:
            name: 工具名称
            
        返回:
            BaseTool: 工具实例
        """
        return self.tool_map.get(name)

    def add_tool(self, tool: BaseTool):
        """
        添加单个工具到集合
        
        参数:
            tool: 要添加的工具
            
        返回:
            ToolCollection: 当前工具集合实例
        """
        self.tools += (tool,)
        self.tool_map[tool.name] = tool
        return self

    def add_tools(self, *tools: BaseTool):
        """
        添加多个工具到集合
        
        参数:
            *tools: 要添加的工具列表
            
        返回:
            ToolCollection: 当前工具集合实例
        """
        for tool in tools:
            self.add_tool(tool)
        return self
