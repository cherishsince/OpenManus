# LLM模块：提供与大语言模型交互的功能
from typing import Dict, List, Literal, Optional, Union

from openai import (
    APIError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.config import LLMSettings, config
from app.logger import logger  # Assuming a logger is set up in your app
from app.schema import Message


class LLM:
    """
    大语言模型接口类：提供与OpenAI API的交互功能
    支持Azure OpenAI和标准OpenAI API
    包含重试机制和错误处理
    """
    _instances: Dict[str, "LLM"] = {}

    def __new__(
        cls, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        """
        实现单例模式的工厂方法
        每个配置名称对应一个唯一的LLM实例
        """
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name, llm_config)
            cls._instances[config_name] = instance
        return cls._instances[config_name]

    def __init__(
        self, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        """
        初始化LLM实例
        设置API配置和客户端连接
        支持Azure OpenAI和标准OpenAI API
        
        参数:
            config_name: 配置名称，默认为"default"
            llm_config: 可选的LLM配置对象
        """
        if not hasattr(self, "client"):  # Only initialize if not already initialized
            llm_config = llm_config or config.llm
            llm_config = llm_config.get(config_name, llm_config["default"])
            self.model = llm_config.model                # 模型名称
            self.max_tokens = llm_config.max_tokens      # 最大令牌数
            self.temperature = llm_config.temperature    # 采样温度
            self.api_type = llm_config.api_type         # API类型
            self.api_key = llm_config.api_key           # API密钥
            self.api_version = llm_config.api_version   # API版本
            self.base_url = llm_config.base_url         # API基础URL
            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def format_messages(messages: List[Union[dict, Message]]) -> List[dict]:
        """
        将消息格式化为LLM可接受的格式

        参数:
            messages: 消息列表，可以是字典或Message对象

        返回:
            List[dict]: OpenAI格式的消息列表

        异常:
            ValueError: 当消息无效或缺少必要字段时
            TypeError: 当提供了不支持的消息类型时

        示例:
            >>> msgs = [
            ...     Message.system_message("你是一个有帮助的助手"),
            ...     {"role": "user", "content": "你好"},
            ...     Message.user_message("你好吗？")
            ... ]
            >>> formatted = LLM.format_messages(msgs)
        """
        formatted_messages = []

        for message in messages:
            if isinstance(message, dict):
                # 如果消息已经是字典格式，确保包含必要字段
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")
                formatted_messages.append(message)
            elif isinstance(message, Message):
                # 如果消息是Message对象，转换为字典
                formatted_messages.append(message.to_dict())
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # 验证所有消息都有必要字段
        for msg in formatted_messages:
            if msg["role"] not in ["system", "user", "assistant", "tool"]:
                raise ValueError(f"Invalid role: {msg['role']}")
            if "content" not in msg and "tool_calls" not in msg:
                raise ValueError(
                    "Message must contain either 'content' or 'tool_calls'"
                )

        return formatted_messages

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        向LLM发送请求并获取响应

        参数:
            messages: 对话消息列表
            system_msgs: 可选的系统消息（将被添加到对话开头）
            stream: 是否使用流式响应
            temperature: 响应的采样温度

        返回:
            str: 生成的响应文本

        异常:
            ValueError: 当消息无效或响应为空时
            OpenAIError: 当API调用在重试后仍然失败时
            Exception: 发生意外错误时
        """
        try:
            # 格式化消息
            formatted_messages = self.format_messages(messages)
            if system_msgs:
                formatted_messages = self.format_messages(system_msgs) + formatted_messages

            # 创建API请求参数
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "stream": stream,
                "temperature": temperature or self.temperature,
            }

            # 发送请求并获取响应
            response = await self.client.chat.completions.create(**params)

            # 处理流式响应
            if stream:
                content = []
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content.append(chunk.choices[0].delta.content)
                return "".join(content)
            
            # 处理非流式响应
            if not response.choices[0].message.content:
                raise ValueError("Empty response from LLM")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Unexpected error in ask: {e}")
            raise

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask_tool(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        timeout: int = 60,
        tools: Optional[List[dict]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        temperature: Optional[float] = None,
        **kwargs,
    ):
        """
        使用函数/工具向LLM发送请求并获取响应

        参数:
            messages: 对话消息列表
            system_msgs: 可选的系统消息
            timeout: 请求超时时间（秒）
            tools: 可用工具列表
            tool_choice: 工具选择策略
            temperature: 响应的采样温度
            **kwargs: 其他补充参数

        返回:
            ChatCompletionMessage: 模型的响应

        异常:
            ValueError: 当工具、工具选择或消息无效时
            OpenAIError: 当API调用在重试后仍然失败时
            Exception: 发生意外错误时
        """
        try:
            # 格式化消息
            formatted_messages = self.format_messages(messages)
            if system_msgs:
                formatted_messages = self.format_messages(system_msgs) + formatted_messages

            # 创建API请求参数
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature or self.temperature,
                "timeout": timeout,
                **kwargs,
            }

            # 添加工具相关参数
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice

            # 发送请求并获取响应
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message

        except Exception as e:
            logger.error(f"Unexpected error in ask_tool: {e}")
            raise
