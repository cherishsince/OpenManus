# 日志模块：配置和管理应用程序的日志记录
import sys
from datetime import datetime

from loguru import logger as _logger

from app.config import PROJECT_ROOT


# 默认控制台输出日志级别
_print_level = "INFO"


def define_log_level(print_level="INFO", logfile_level="DEBUG", name: str = None):
    """
    配置日志级别和输出方式
    
    参数:
        print_level: 控制台输出的日志级别，默认为"INFO"
        logfile_level: 文件输出的日志级别，默认为"DEBUG"
        name: 日志文件名前缀，可选
        
    返回:
        logger: 配置好的日志记录器
        
    Adjust the log level to above level
    """
    global _print_level
    _print_level = print_level

    # 生成日志文件名，包含时间戳
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d%H%M%S")
    log_name = (
        f"{name}_{formatted_date}" if name else formatted_date
    )  # 使用前缀名称命名日志文件

    # 重新配置日志记录器
    _logger.remove()  # 移除默认处理器
    _logger.add(sys.stderr, level=print_level)  # 添加控制台输出处理器
    _logger.add(PROJECT_ROOT / f"logs/{log_name}.log", level=logfile_level)  # 添加文件输出处理器
    return _logger


# 创建全局日志记录器
logger = define_log_level()


if __name__ == "__main__":
    # 测试各种日志级别
    logger.info("启动应用程序")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误信息")

    # 测试异常记录
    try:
        raise ValueError("测试错误")
    except Exception as e:
        logger.exception(f"发生错误：{e}")
