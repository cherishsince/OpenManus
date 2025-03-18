# 软件工程代理模块：实现自主编程代理，能够直接与计算机交互完成任务
from typing import List

from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.prompt.swe import NEXT_STEP_TEMPLATE, SYSTEM_PROMPT
from app.tool import Bash, StrReplaceEditor, Terminate, ToolCollection


class SWEAgent(ToolCallAgent):
    """
    软件工程代理：实现代码执行和自然对话的自主编程代理
    An agent that implements the SWEAgent paradigm for executing code and natural conversations.
    """

    # 代理基本信息
    name: str = "swe"  # 代理名称
    description: str = "an autonomous AI programmer that interacts directly with the computer to solve tasks."  # 代理描述

    # 提示词模板
    system_prompt: str = SYSTEM_PROMPT  # 系统提示词
    next_step_prompt: str = NEXT_STEP_TEMPLATE  # 下一步提示词模板

    # 可用工具配置
    available_tools: ToolCollection = ToolCollection(
        Bash(), StrReplaceEditor(), Terminate()
    )  # 可用工具集合
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])  # 特殊工具名称列表

    # 执行限制
    max_steps: int = 30  # 最大执行步数

    # 工作环境配置
    bash: Bash = Field(default_factory=Bash)  # Bash工具实例
    working_dir: str = "."  # 当前工作目录

    async def think(self) -> bool:
        """
        处理当前状态并决定下一步行动
        
        返回:
            bool: 是否继续执行
            
        Process current state and decide next action
        """
        # 更新工作目录
        self.working_dir = await self.bash.execute("pwd")
        # 使用当前工作目录更新下一步提示词
        self.next_step_prompt = self.next_step_prompt.format(
            current_dir=self.working_dir
        )

        return await super().think()
