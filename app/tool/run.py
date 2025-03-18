"""
Shell命令异步执行工具
支持超时控制和输出截断功能
Utility to run shell commands asynchronously with a timeout.
"""

import asyncio


# 输出截断提示信息
TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"
# 最大响应长度（字符数）
MAX_RESPONSE_LEN: int = 16000


def maybe_truncate(content: str, truncate_after: int | None = MAX_RESPONSE_LEN):
    """
    如果内容超过指定长度则进行截断
    
    参数:
        content: 需要处理的内容字符串
        truncate_after: 截断长度阈值，默认为MAX_RESPONSE_LEN
        
    返回:
        str: 处理后的内容（可能被截断）
    
    Truncate content and append a notice if content exceeds the specified length.
    """
    return (
        content
        if not truncate_after or len(content) <= truncate_after
        else content[:truncate_after] + TRUNCATED_MESSAGE
    )


async def run(
    cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN,
):
    """
    异步执行shell命令，支持超时控制
    
    参数:
        cmd: 要执行的shell命令
        timeout: 超时时间（秒），默认120秒
        truncate_after: 输出截断长度，默认为MAX_RESPONSE_LEN
        
    返回:
        tuple: (返回码, 标准输出, 标准错误输出)
        
    异常:
        TimeoutError: 当命令执行超时时抛出
    
    Run a shell command asynchronously with a timeout.
    """
    # 创建子进程执行命令
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        # 等待进程完成并获取输出
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return (
            process.returncode or 0,
            maybe_truncate(stdout.decode(), truncate_after=truncate_after),
            maybe_truncate(stderr.decode(), truncate_after=truncate_after),
        )
    except asyncio.TimeoutError as exc:
        # 超时时尝试终止进程
        try:
            process.kill()
        except ProcessLookupError:
            pass
        raise TimeoutError(
            f"Command '{cmd}' timed out after {timeout} seconds"
        ) from exc
