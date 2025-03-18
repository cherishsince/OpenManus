import asyncio
import json
from typing import Optional

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext
from browser_use.dom.service import DomService
from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.tool.base import BaseTool, ToolResult


_BROWSER_DESCRIPTION = """
Interact with a web browser to perform various actions such as navigation, element interaction,
content extraction, and tab management. Supported actions include:
- 'navigate': Go to a specific URL
- 'click': Click an element by index
- 'input_text': Input text into an element
- 'screenshot': Capture a screenshot
- 'get_html': Get page HTML content
- 'get_text': Get text content of the page
- 'read_links': Get all links on the page
- 'execute_js': Execute JavaScript code
- 'scroll': Scroll the page
- 'switch_tab': Switch to a specific tab
- 'new_tab': Open a new tab
- 'close_tab': Close the current tab
- 'refresh': Refresh the current page
"""


class BrowserUseTool(BaseTool):
    """
    浏览器使用工具：用于与网页浏览器交互的工具类
    
    支持导航、元素交互、内容提取和标签页管理等多种操作。
    """

    name: str = "browser_use"  # 工具名称
    description: str = _BROWSER_DESCRIPTION  # 工具描述
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "navigate",  # 导航到指定URL
                    "click",  # 点击指定索引的元素
                    "input_text",  # 向元素输入文本
                    "screenshot",  # 捕获截图
                    "get_html",  # 获取页面HTML内容
                    "get_text",  # 获取页面文本内容
                    "execute_js",  # 执行JavaScript代码
                    "scroll",  # 滚动页面
                    "switch_tab",  # 切换到指定标签页
                    "new_tab",  # 打开新标签页
                    "close_tab",  # 关闭当前标签页
                    "refresh",  # 刷新当前页面
                ],
                "description": "The browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL for 'navigate' or 'new_tab' actions",
            },
            "index": {
                "type": "integer",
                "description": "Element index for 'click' or 'input_text' actions",
            },
            "text": {"type": "string", "description": "Text for 'input_text' action"},
            "script": {
                "type": "string",
                "description": "JavaScript code for 'execute_js' action",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Pixels to scroll (positive for down, negative for up) for 'scroll' action",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID for 'switch_tab' action",
            },
        },
        "required": ["action"],
        "dependencies": {
            "navigate": ["url"],
            "click": ["index"],
            "input_text": ["index", "text"],
            "execute_js": ["script"],
            "switch_tab": ["tab_id"],
            "new_tab": ["url"],
            "scroll": ["scroll_amount"],
        },
    }

    lock: asyncio.Lock = Field(default_factory=asyncio.Lock)  # 异步锁，用于线程安全
    browser: Optional[BrowserUseBrowser] = Field(default=None, exclude=True)  # 浏览器实例
    context: Optional[BrowserContext] = Field(default=None, exclude=True)  # 浏览器上下文
    dom_service: Optional[DomService] = Field(default=None, exclude=True)  # DOM服务实例

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        """
        验证参数：确保参数不为空
        
        参数:
            v: 参数字典
            info: 验证信息
            
        返回:
            dict: 验证后的参数字典
            
        异常:
            ValueError: 当参数为空时
        """
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v

    async def _ensure_browser_initialized(self) -> BrowserContext:
        """
        确保浏览器和上下文已初始化
        
        返回:
            BrowserContext: 浏览器上下文
        """
        if self.browser is None:
            self.browser = BrowserUseBrowser(BrowserConfig(headless=False))
        if self.context is None:
            self.context = await self.browser.new_context()
            self.dom_service = DomService(await self.context.get_current_page())
        return self.context

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        script: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """
        执行指定的浏览器操作
        
        参数:
            action: 要执行的浏览器操作
            url: 导航或新标签页的URL
            index: 点击或输入操作的元素索引
            text: 输入操作的文本
            script: 要执行的JavaScript代码
            scroll_amount: 滚动操作的像素数
            tab_id: 切换标签页的标签ID
            **kwargs: 其他参数
            
        返回:
            ToolResult: 包含操作输出或错误的结果
        """
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()

                if action == "navigate":
                    if not url:
                        return ToolResult(error="URL is required for 'navigate' action")
                    await context.navigate_to(url)
                    return ToolResult(output=f"Navigated to {url}")

                elif action == "click":
                    if index is None:
                        return ToolResult(error="Index is required for 'click' action")
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    download_path = await context._click_element_node(element)
                    output = f"Clicked element at index {index}"
                    if download_path:
                        output += f" - Downloaded file to {download_path}"
                    return ToolResult(output=output)

                elif action == "input_text":
                    if index is None or not text:
                        return ToolResult(
                            error="Index and text are required for 'input_text' action"
                        )
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    await context._input_text_element_node(element, text)
                    return ToolResult(
                        output=f"Input '{text}' into element at index {index}"
                    )

                elif action == "screenshot":
                    screenshot = await context.take_screenshot(full_page=True)
                    return ToolResult(
                        output=f"Screenshot captured (base64 length: {len(screenshot)})",
                        system=screenshot,
                    )

                elif action == "get_html":
                    html = await context.get_page_html()
                    truncated = html[:2000] + "..." if len(html) > 2000 else html
                    return ToolResult(output=truncated)

                elif action == "get_text":
                    text = await context.execute_javascript("document.body.innerText")
                    return ToolResult(output=text)

                elif action == "read_links":
                    links = await context.execute_javascript(
                        "document.querySelectorAll('a[href]').forEach((elem) => {if (elem.innerText) {console.log(elem.innerText, elem.href)}})"
                    )
                    return ToolResult(output=links)

                elif action == "execute_js":
                    if not script:
                        return ToolResult(
                            error="Script is required for 'execute_js' action"
                        )
                    result = await context.execute_javascript(script)
                    return ToolResult(output=str(result))

                elif action == "scroll":
                    if scroll_amount is None:
                        return ToolResult(
                            error="Scroll amount is required for 'scroll' action"
                        )
                    await context.execute_javascript(
                        f"window.scrollBy(0, {scroll_amount});"
                    )
                    direction = "down" if scroll_amount > 0 else "up"
                    return ToolResult(
                        output=f"Scrolled {direction} by {abs(scroll_amount)} pixels"
                    )

                elif action == "switch_tab":
                    if tab_id is None:
                        return ToolResult(
                            error="Tab ID is required for 'switch_tab' action"
                        )
                    await context.switch_to_tab(tab_id)
                    return ToolResult(output=f"Switched to tab {tab_id}")

                elif action == "new_tab":
                    if not url:
                        return ToolResult(error="URL is required for 'new_tab' action")
                    await context.create_new_tab(url)
                    return ToolResult(output=f"Opened new tab with URL {url}")

                elif action == "close_tab":
                    await context.close_current_tab()
                    return ToolResult(output="Closed current tab")

                elif action == "refresh":
                    await context.refresh_page()
                    return ToolResult(output="Refreshed current page")

                else:
                    return ToolResult(error=f"Unknown action: {action}")

            except Exception as e:
                return ToolResult(error=f"Browser action '{action}' failed: {str(e)}")

    async def get_current_state(self) -> ToolResult:
        """
        获取当前浏览器状态
        
        返回:
            ToolResult: 包含当前状态的结果
        """
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                state = await context.get_state()
                return ToolResult(output=json.dumps(state, indent=2))
            except Exception as e:
                return ToolResult(error=f"Failed to get browser state: {str(e)}")

    async def cleanup(self):
        """
        清理资源：关闭浏览器和上下文
        """
        async with self.lock:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()

    def __del__(self):
        """
        析构函数：确保资源被正确清理
        """
        asyncio.create_task(self.cleanup())
