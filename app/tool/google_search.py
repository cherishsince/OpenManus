import asyncio
from typing import List

from googlesearch import search

from app.tool.base import BaseTool


class GoogleSearch(BaseTool):
    """
    Google搜索工具：用于执行Google搜索并返回相关链接列表的工具类
    
    支持在网络上查找信息、获取最新数据或研究特定主题。
    该工具返回与搜索查询匹配的URL列表。
    """

    name: str = "google_search"  # 工具名称
    description: str = """Perform a Google search and return a list of relevant links.
Use this tool when you need to find information on the web, get up-to-date data, or research specific topics.
The tool returns a list of URLs that match the search query.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "(required) The search query to submit to Google.",  # 提交给Google的搜索查询
            },
            "num_results": {
                "type": "integer",
                "description": "(optional) The number of search results to return. Default is 10.",  # 返回的搜索结果数量，默认为10
                "default": 10,
            },
        },
        "required": ["query"],  # 必需参数
    }

    async def execute(self, query: str, num_results: int = 10) -> List[str]:
        """
        执行Google搜索并返回URL列表
        
        参数:
            query (str): 提交给Google的搜索查询
            num_results (int, optional): 返回的搜索结果数量，默认为10
            
        返回:
            List[str]: 与搜索查询匹配的URL列表
        """
        # 在线程池中运行搜索以防止阻塞
        loop = asyncio.get_event_loop()
        links = await loop.run_in_executor(
            None, lambda: list(search(query, num_results=num_results))
        )

        return links
