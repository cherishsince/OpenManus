# 工具基类模块：定义工具的基本接口和结果类型
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseTool(ABC, BaseModel):
    """
    工具基类：定义所有工具的通用接口
    继承自ABC（抽象基类）和BaseModel（Pydantic模型）
    """
    name: str  # 工具名称
    description: str  # 工具描述
    parameters: Optional[dict] = None  # 工具参数定义

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型

    async def __call__(self, **kwargs) -> Any:
        """
        工具调用入口
        允许像函数一样调用工具实例
        """
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行工具的抽象方法
        所有工具子类必须实现此方法
        """
        pass

    def to_param(self) -> Dict:
        """
        将工具转换为函数调用格式
        用于与LLM的函数调用接口集成
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolResult(BaseModel):
    """
    工具执行结果类：表示工具执行的结果
    包含输出、错误和系统信息
    """

    output: Any = Field(default=None)  # 工具输出
    error: Optional[str] = Field(default=None)  # 错误信息
    system: Optional[str] = Field(default=None)  # 系统信息

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型

    def __bool__(self):
        """
        布尔值转换：当任何字段有值时返回True
        """
        return any(getattr(self, field) for field in self.__fields__)

    def __add__(self, other: "ToolResult"):
        """
        结果合并：合并两个工具结果
        
        参数:
            other: 另一个工具结果
            
        返回:
            ToolResult: 合并后的结果
            
        异常:
            ValueError: 当结果无法合并时
        """
        def combine_fields(
            field: Optional[str], other_field: Optional[str], concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("无法合并工具结果")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            system=combine_fields(self.system, other.system),
        )

    def __str__(self):
        """字符串表示：优先显示错误信息"""
        return f"错误：{self.error}" if self.error else self.output

    def replace(self, **kwargs):
        """
        替换字段：返回一个字段被替换的新结果对象
        
        参数:
            **kwargs: 要替换的字段和新值
        """
        return type(self)(**{**self.dict(), **kwargs})


class CLIResult(ToolResult):
    """命令行结果类：可以渲染为命令行输出的工具结果"""


class ToolFailure(ToolResult):
    """失败结果类：表示工具执行失败的结果"""


class AgentAwareTool:
    """代理感知工具类：可以访问代理实例的工具基类"""
    agent: Optional = None  # 关联的代理实例
