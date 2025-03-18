import os

import aiofiles

from app.tool.base import BaseTool


class FileSaver(BaseTool):
    """
    文件保存工具：用于将内容保存到本地文件的工具类
    
    支持将文本、代码或生成的内容保存到本地文件系统。
    该工具接受内容和文件路径作为参数，并将内容保存到指定位置。
    """

    name: str = "file_saver"  # 工具名称
    description: str = """Save content to a local file at a specified path.
Use this tool when you need to save text, code, or generated content to a file on the local filesystem.
The tool accepts content and a file path, and saves the content to that location.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "(required) The content to save to the file.",  # 要保存到文件的内容
            },
            "file_path": {
                "type": "string",
                "description": "(required) The path where the file should be saved, including filename and extension.",  # 文件保存路径，包括文件名和扩展名
            },
            "mode": {
                "type": "string",
                "description": "(optional) The file opening mode. Default is 'w' for write. Use 'a' for append.",  # 文件打开模式，默认为写入模式，可选追加模式
                "enum": ["w", "a"],
                "default": "w",
            },
        },
        "required": ["content", "file_path"],  # 必需参数
    }

    async def execute(self, content: str, file_path: str, mode: str = "w") -> str:
        """
        将内容保存到指定路径的文件中
        
        参数:
            content (str): 要保存到文件的内容
            file_path (str): 文件保存路径
            mode (str, optional): 文件打开模式，默认为写入模式，可选追加模式
            
        返回:
            str: 操作结果消息
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # 直接写入文件
            async with aiofiles.open(file_path, mode, encoding="utf-8") as file:
                await file.write(content)

            return f"Content successfully saved to {file_path}"
        except Exception as e:
            return f"Error saving file: {str(e)}"
