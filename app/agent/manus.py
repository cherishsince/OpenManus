from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.file_saver import FileSaver
from app.tool.google_search import GoogleSearch
from app.tool.python_execute import PythonExecute


class Manus(ToolCallAgent):
    """
    一个多功能的通用代理，使用规划来解决各种任务。

    这个代理扩展了 PlanningAgent，具有全面的工具集和功能，
    包括 Python 执行、网页浏览、文件操作和信息检索，
    可以处理广泛的用户请求。

    A versatile general-purpose agent that uses planning to solve various tasks.

    This agent extends PlanningAgent with a comprehensive set of tools and capabilities,
    including Python execution, web browsing, file operations, and information retrieval
    to handle a wide range of user requests.
    """

    name: str = "Manus"  # 代理名称
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools"  # 代理描述：一个可以使用多种工具解决各种任务的通用代理
    )

    system_prompt: str = SYSTEM_PROMPT  # 系统提示词
    next_step_prompt: str = NEXT_STEP_PROMPT  # 下一步提示词

    # 添加通用工具到工具集合
    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),  # Python 执行工具
            GoogleSearch(),  # Google 搜索工具
            BrowserUseTool(),  # 浏览器使用工具
            FileSaver(),  # 文件保存工具
            Terminate()  # 终止工具
        )
    )
