from app.tool.base import BaseTool


_TERMINATE_DESCRIPTION = """Terminate the interaction when the request is met OR if the assistant cannot proceed further with the task."""


class Terminate(BaseTool):
    """
    终止工具：用于结束当前交互的工具类
    
    当请求已满足或助手无法继续执行任务时使用。
    """

    name: str = "terminate"  # 工具名称
    description: str = _TERMINATE_DESCRIPTION  # 工具描述
    parameters: dict = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "The finish status of the interaction.",  # 交互的结束状态
                "enum": ["success", "failure"],  # 可选值：成功或失败
            }
        },
        "required": ["status"],  # 必需参数
    }

    async def execute(self, status: str) -> str:
        """
        结束当前执行
        
        参数:
            status: 结束状态
            
        返回:
            str: 包含结束状态的消息
        """
        return f"The interaction has been completed with status: {status}"
