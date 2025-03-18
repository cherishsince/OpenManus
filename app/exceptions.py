# 异常模块：定义应用程序中使用的自定义异常类

class ToolError(Exception):
    """
    工具错误异常：当工具执行过程中遇到错误时抛出
    Raised when a tool encounters an error.
    """

    def __init__(self, message):
        """
        初始化工具错误异常
        
        参数:
            message: 错误信息
        """
        self.message = message
