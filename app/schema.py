# 模式定义模块：定义应用程序中使用的数据模型和状态
from enum import Enum
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent execution states"""
    # 代理执行状态枚举

    IDLE = "IDLE"           # 空闲状态
    RUNNING = "RUNNING"     # 运行状态
    FINISHED = "FINISHED"   # 完成状态
    ERROR = "ERROR"         # 错误状态


class Function(BaseModel):
    """函数调用的参数模型"""
    name: str        # 函数名称
    arguments: str   # 函数参数


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""
    # 表示消息中的工具/函数调用

    id: str                     # 调用ID
    type: str = "function"      # 调用类型，默认为function
    function: Function          # 函数信息


class Message(BaseModel):
    """Represents a chat message in the conversation"""
    # 表示对话中的消息

    role: Literal["system", "user", "assistant", "tool"] = Field(...)  # 消息角色
    content: Optional[str] = Field(default=None)                       # 消息内容
    tool_calls: Optional[List[ToolCall]] = Field(default=None)        # 工具调用列表
    name: Optional[str] = Field(default=None)                         # 消息名称
    tool_call_id: Optional[str] = Field(default=None)                 # 工具调用ID

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        # 将消息转换为字典格式
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.dict() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        return message

    @classmethod
    def user_message(cls, content: str) -> "Message":
        """Create a user message"""
        # 创建用户消息
        return cls(role="user", content=content)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        # 创建系统消息
        return cls(role="system", content=content)

    @classmethod
    def assistant_message(cls, content: Optional[str] = None) -> "Message":
        """Create an assistant message"""
        # 创建助手消息
        return cls(role="assistant", content=content)

    @classmethod
    def tool_message(cls, content: str, name, tool_call_id: str) -> "Message":
        """Create a tool message"""
        # 创建工具消息
        return cls(role="tool", content=content, name=name, tool_call_id=tool_call_id)

    @classmethod
    def from_tool_calls(
        cls, tool_calls: List[Any], content: Union[str, List[str]] = "", **kwargs
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
        """
        # 从原始工具调用创建工具调用消息
        formatted_calls = [
            {"id": call.id, "function": call.function.model_dump(), "type": "function"}
            for call in tool_calls
        ]
        return cls(
            role="assistant", content=content, tool_calls=formatted_calls, **kwargs
        )


class Memory(BaseModel):
    """内存管理类：存储和管理对话消息"""
    messages: List[Message] = Field(default_factory=list)  # 消息列表
    max_messages: int = Field(default=100)                # 最大消息数量

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        # 向内存添加消息
        self.messages.append(message)
        # Optional: Implement message limit
        # 可选：实现消息数量限制
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple messages to memory"""
        # 向内存添加多条消息
        self.messages.extend(messages)

    def clear(self) -> None:
        """Clear all messages"""
        # 清空所有消息
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages"""
        # 获取最近的n条消息
        return self.messages[-n:]

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        # 将消息列表转换为字典列表
        return [msg.to_dict() for msg in self.messages]
