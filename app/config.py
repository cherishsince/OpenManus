# 配置模块：管理应用程序的配置信息
import threading
import tomllib
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field
from app.logger import logger


def get_project_root() -> Path:
    """
    获取项目根目录
    Get the project root directory
    """
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


class LLMSettings:
    """
    LLM配置类：管理大语言模型的配置参数
    支持Azure OpenAI和标准OpenAI API的配置
    """

    def __init__(self, config: Dict):
        """
        初始化LLM配置
        
        参数:
            config: 配置字典，包含LLM的所有配置参数
        """
        self.config = config

    def __getitem__(self, key: str) -> "LLMSettings":
        """
        通过键获取配置
        支持使用点号访问嵌套配置
        
        参数:
            key: 配置键名
            
        返回:
            LLMSettings: 对应的配置对象
        """
        return LLMSettings(self.config[key])

    def get(self, key: str, default: Optional[Dict] = None) -> "LLMSettings":
        """
        安全地获取配置，支持默认值
        
        参数:
            key: 配置键名
            default: 默认配置字典
            
        返回:
            LLMSettings: 对应的配置对象
        """
        return LLMSettings(self.config.get(key, default or {}))

    @property
    def model(self) -> str:
        """获取模型名称"""
        return self.config.get("model", "gpt-4")

    @property
    def max_tokens(self) -> int:
        """获取最大令牌数"""
        return self.config.get("max_tokens", 4096)

    @property
    def temperature(self) -> float:
        """获取采样温度"""
        return self.config.get("temperature", 0.7)

    @property
    def api_type(self) -> str:
        """获取API类型（azure或openai）"""
        return self.config.get("api_type", "openai")

    @property
    def api_key(self) -> str:
        """获取API密钥"""
        return self.config.get("api_key", "")

    @property
    def api_version(self) -> str:
        """获取API版本"""
        return self.config.get("api_version", "2024-02-15-preview")

    @property
    def base_url(self) -> str:
        """获取API基础URL"""
        return self.config.get("base_url", "https://api.openai.com/v1")


class AppConfig(BaseModel):
    """
    应用程序配置模型：包含所有LLM配置
    支持多个LLM配置实例
    """
    llm: Dict[str, LLMSettings]


class Config:
    """
    配置管理类：实现单例模式，确保全局配置一致性
    负责加载和管理配置文件
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        """
        实现单例模式：确保只创建一个配置实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化配置：仅在第一次创建实例时加载配置
        使用线程锁确保线程安全
        """
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        """
        获取配置文件路径
        优先使用config.toml，如果不存在则使用config.example.toml
        
        返回:
            Path: 配置文件路径
            
        异常:
            FileNotFoundError: 当找不到任何配置文件时
        """
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("未在config目录中找到配置文件")

    def _load_config(self) -> dict:
        """
        加载TOML配置文件
        
        返回:
            dict: 解析后的配置字典
        """
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        """
        加载初始配置
        设置LLM配置并记录日志
        """
        try:
            self._config = self._load_config()
            logger.info(f"已从{self._get_config_path()}加载配置")
        except Exception as e:
            logger.error(f"加载配置时出错：{e}")
            self._config = {}

    @property
    def llm(self) -> LLMSettings:
        """
        获取LLM配置
        
        返回:
            LLMSettings: LLM配置对象
        """
        return LLMSettings(self._config.get("llm", {}))

    def reload(self):
        """重新加载配置文件"""
        with self._lock:
            self._config = self._load_config()
            logger.info("配置已重新加载")


# 创建全局配置实例
config = Config()
