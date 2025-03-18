from abc import ABC, abstractmethod
from typing import Optional

from pydantic import Field

from app.agent.base import BaseAgent
from app.llm import LLM
from app.schema import AgentState, Memory


class ReActAgent(BaseAgent, ABC):
    """
    ReAct代理基类：实现思考-行动-观察循环的代理框架
    
    这个代理框架基于ReAct（Reasoning and Acting）范式，
    将代理的行为分解为思考（think）和行动（act）两个阶段。
    """
    
    name: str  # 代理名称
    description: Optional[str] = None  # 代理描述

    system_prompt: Optional[str] = None  # 系统提示词
    next_step_prompt: Optional[str] = None  # 下一步提示词

    llm: Optional[LLM] = Field(default_factory=LLM)  # 语言模型实例
    memory: Memory = Field(default_factory=Memory)  # 内存存储
    state: AgentState = AgentState.IDLE  # 代理状态

    max_steps: int = 10  # 最大执行步数
    current_step: int = 0  # 当前执行步数

    @abstractmethod
    async def think(self) -> bool:
        """
        思考阶段：处理当前状态并决定下一步行动
        
        返回:
            bool: 是否需要执行行动
            
        Process current state and decide next action
        """

    @abstractmethod
    async def act(self) -> str:
        """
        行动阶段：执行已决定的行动
        
        返回:
            str: 行动执行的结果
            
        Execute decided actions
        """

    async def step(self) -> str:
        """
        执行一个完整的思考-行动步骤
        
        返回:
            str: 步骤执行的结果
            
        Execute a single step: think and act.
        """
        should_act = await self.think()
        if not should_act:
            return "思考完成 - 无需行动"  # Thinking complete - no action needed
        return await self.act()
