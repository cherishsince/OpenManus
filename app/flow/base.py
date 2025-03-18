# 流程基类模块：定义支持多代理执行的基本流程接口
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from app.agent.base import BaseAgent


# 流程类型枚举
class FlowType(str, Enum):
    PLANNING = "planning"  # 规划流程类型


class BaseFlow(BaseModel, ABC):
    """Base class for execution flows supporting multiple agents"""
    # 执行流程的基类，支持多个代理的协同工作

    # 代理字典，键为代理名称，值为代理实例
    agents: Dict[str, BaseAgent]
    # 可选的工具列表
    tools: Optional[List] = None
    # 主要代理的键名
    primary_agent_key: Optional[str] = None

    class Config:
        # 允许任意类型
        arbitrary_types_allowed = True

    def __init__(
        self, agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], **data
    ):
        # Handle different ways of providing agents
        # 处理不同方式提供的代理参数
        if isinstance(agents, BaseAgent):
            agents_dict = {"default": agents}
        elif isinstance(agents, list):
            agents_dict = {f"agent_{i}": agent for i, agent in enumerate(agents)}
        else:
            agents_dict = agents

        # If primary agent not specified, use first agent
        # 如果未指定主要代理，使用第一个代理作为主要代理
        primary_key = data.get("primary_agent_key")
        if not primary_key and agents_dict:
            primary_key = next(iter(agents_dict))
            data["primary_agent_key"] = primary_key

        # Set the agents dictionary
        # 设置代理字典
        data["agents"] = agents_dict

        # Initialize using BaseModel's init
        # 使用BaseModel的初始化方法
        super().__init__(**data)

    @property
    def primary_agent(self) -> Optional[BaseAgent]:
        """Get the primary agent for the flow"""
        # 获取流程的主要代理
        return self.agents.get(self.primary_agent_key)

    def get_agent(self, key: str) -> Optional[BaseAgent]:
        """Get a specific agent by key"""
        # 通过键名获取特定的代理
        return self.agents.get(key)

    def add_agent(self, key: str, agent: BaseAgent) -> None:
        """Add a new agent to the flow"""
        # 向流程中添加新的代理
        self.agents[key] = agent

    @abstractmethod
    async def execute(self, input_text: str) -> str:
        """Execute the flow with given input"""
        # 执行流程，处理给定的输入文本
