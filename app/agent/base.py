# 代理基类模块：定义代理的基本接口和状态管理
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Memory, Message


class BaseAgent(BaseModel, ABC):
    """
    代理基类：管理代理状态和执行流程的抽象基类
    
    提供状态转换、内存管理和基于步骤的执行循环的基础功能
    子类必须实现step方法来定义具体行为
    
    Abstract base class for managing agent state and execution.

    Provides foundational functionality for state transitions, memory management,
    and a step-based execution loop. Subclasses must implement the `step` method.
    """

    # 核心属性
    name: str = Field(..., description="代理的唯一名称")  # 代理名称
    description: Optional[str] = Field(None, description="代理的可选描述")  # 代理描述

    # 提示词配置
    system_prompt: Optional[str] = Field(
        None, description="系统级指令提示词"  # 系统提示词
    )
    next_step_prompt: Optional[str] = Field(
        None, description="决定下一步行动的提示词"  # 下一步提示词
    )

    # 依赖组件
    llm: LLM = Field(default_factory=LLM, description="语言模型实例")  # LLM实例
    memory: Memory = Field(default_factory=Memory, description="代理的内存存储")  # 内存存储
    state: AgentState = Field(
        default=AgentState.IDLE, description="代理的当前状态"  # 当前状态
    )

    # 执行控制
    max_steps: int = Field(default=10, description="终止前的最大步数")  # 最大步数
    current_step: int = Field(default=0, description="执行中的当前步数")  # 当前步数

    duplicate_threshold: int = 2  # 重复检测阈值

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型
        extra = "allow"  # 允许子类添加额外字段

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """
        初始化代理：如果未提供则使用默认设置
        
        返回:
            BaseAgent: 初始化后的代理实例
        """
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """
        代理状态转换的上下文管理器
        
        参数:
            new_state: 要转换到的新状态
            
        异常:
            ValueError: 当new_state无效时
            
        Context manager for safe agent state transitions.
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"无效的状态：{new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # 发生错误时转换到ERROR状态
            raise e
        finally:
            self.state = previous_state  # 恢复到之前的状态

    def update_memory(
        self,
        role: Literal["user", "system", "assistant", "tool"],
        content: str,
        **kwargs,
    ) -> None:
        """
        向代理的内存添加消息
        
        参数:
            role: 消息发送者的角色（用户、系统、助手、工具）
            content: 消息内容
            **kwargs: 附加参数（例如工具消息的tool_call_id）
            
        异常:
            ValueError: 当角色不受支持时
            
        Add a message to the agent's memory.
        """
        message_map = {
            "user": Message.user_message,  # 用户消息
            "system": Message.system_message,  # 系统消息
            "assistant": Message.assistant_message,  # 助手消息
            "tool": lambda content, **kw: Message.tool_message(content, **kw),  # 工具消息
        }

        if role not in message_map:
            raise ValueError(f"不支持的消息角色：{role}")

        msg_factory = message_map[role]
        msg = msg_factory(content, **kwargs) if role == "tool" else msg_factory(content)
        self.memory.add_message(msg)

    async def run(self, request: Optional[str] = None) -> str:
        """
        异步执行代理的主循环
        
        参数:
            request: 可选的初始用户请求
            
        返回:
            str: 执行结果的摘要
            
        异常:
            RuntimeError: 当代理不在IDLE状态时
            
        Execute the agent's main loop asynchronously.
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"无法从状态{self.state}启动代理")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"执行步骤 {self.current_step}/{self.max_steps}")
                step_result = await self.step()

                # 检查是否陷入循环
                if self.is_stuck():
                    self.handle_stuck_state()

                results.append(f"步骤 {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                results.append(f"终止：达到最大步数（{self.max_steps}）")

        return "\n".join(results) if results else "未执行任何步骤"

    @abstractmethod
    async def step(self) -> str:
        """
        执行代理工作流中的单个步骤
        
        子类必须实现此方法以定义具体行为
        
        返回:
            str: 步骤执行的结果
            
        Execute a single step in the agent's workflow.
        """
        pass

    def handle_stuck_state(self):
        """
        处理陷入循环的状态
        通过添加提示词来改变策略
        
        Handle stuck state by adding a prompt to change strategy
        """
        stuck_prompt = "\
        检测到重复响应。请考虑新的策略，避免重复已经尝试过的无效路径。"
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"代理检测到陷入循环。添加提示词：{stuck_prompt}")

    def is_stuck(self) -> bool:
        """
        检查代理是否陷入循环
        通过检测重复内容来判断
        
        返回:
            bool: 是否陷入循环
            
        Check if the agent is stuck in a loop by detecting duplicate content
        """
        if len(self.memory.messages) < 2:
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # 计算相同内容出现的次数
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )

        return duplicate_count >= self.duplicate_threshold

    @property
    def messages(self) -> List[Message]:
        """
        获取代理内存中的消息列表
        
        返回:
            List[Message]: 消息列表
            
        Retrieve a list of messages from the agent's memory.
        """
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """
        设置代理内存中的消息列表
        
        参数:
            value: 新的消息列表
            
        Set the list of messages in the agent's memory.
        """
        self.memory.messages = value
