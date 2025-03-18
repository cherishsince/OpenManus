from abc import ABC, abstractmethod
from typing import Optional

from pydantic import Field

from app.agent.base import BaseAgent
from app.llm import LLM
from app.schema import AgentState, Memory


class ReActAgent(BaseAgent, ABC):
    """ReAct (Reasoning and Acting) agent base class.

    Implements the ReAct pattern for AI agents that alternate between
    reasoning about their current state and taking actions.

    ReAct（推理和行动）代理基类。

    实现了AI代理的ReAct模式，在推理当前状态和采取行动之间交替进行。
    """

    name: str
    description: Optional[str] = None

    system_prompt: Optional[str] = None
    next_step_prompt: Optional[str] = None

    llm: Optional[LLM] = Field(default_factory=LLM)
    memory: Memory = Field(default_factory=Memory)
    state: AgentState = AgentState.IDLE

    max_steps: int = 10
    current_step: int = 0

    @abstractmethod
    async def think(self) -> bool:
        """Process current state and decide next action.

        处理当前状态并决定下一步行动。
        """

    @abstractmethod
    async def act(self) -> str:
        """Execute decided actions.

        执行已决定的行动。
        """

    async def step(self) -> str:
        """Execute a single step: think and act.

        执行单个步骤：思考和行动。
        """
        should_act = await self.think()
        if not should_act:
            return "Thinking complete - no action needed"
        return await self.act()
