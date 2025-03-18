import threading
from typing import Dict

from app.tool.base import BaseTool


class PythonExecute(BaseTool):
    """
    Python代码执行工具：用于执行Python代码的工具类，具有超时和安全限制功能
    
    注意：只能看到print输出，函数返回值不会被捕获。使用print语句来查看结果。
    """

    name: str = "python_execute"  # 工具名称
    description: str = "Executes Python code string. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",  # 要执行的Python代码
            },
        },
        "required": ["code"],  # 必需参数
    }

    async def execute(
        self,
        code: str,
        timeout: int = 5,
    ) -> Dict:
        """
        执行提供的Python代码，带有超时限制
        
        参数:
            code (str): 要执行的Python代码
            timeout (int): 执行超时时间（秒）
            
        返回:
            Dict: 包含执行输出或错误消息的'observation'和'success'状态
        """
        result = {"observation": ""}

        def run_code():
            try:
                # 创建安全的全局命名空间
                safe_globals = {"__builtins__": dict(__builtins__)}

                import sys
                from io import StringIO

                # 重定向标准输出到StringIO缓冲区
                output_buffer = StringIO()
                sys.stdout = output_buffer

                # 执行代码
                exec(code, safe_globals, {})

                # 恢复标准输出
                sys.stdout = sys.__stdout__

                # 获取输出内容
                result["observation"] = output_buffer.getvalue()

            except Exception as e:
                result["observation"] = str(e)
                result["success"] = False

        # 在新线程中运行代码
        thread = threading.Thread(target=run_code)
        thread.start()
        thread.join(timeout)

        # 检查是否超时
        if thread.is_alive():
            return {
                "observation": f"Execution timeout after {timeout} seconds",
                "success": False,
            }

        return result
