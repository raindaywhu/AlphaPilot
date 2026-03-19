#!/usr/bin/env python3
"""
统一配置管理模块

所有配置项统一管理，包括 API Keys、模型参数等。
支持从环境变量或 .env 文件加载。
"""

import os
from typing import Optional

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 未安装时跳过


class Config:
    """统一配置类"""
    
    # ========== LLM 配置 ==========
    # 智谱 AI GLM-5 API
    GLM_API_KEY: str = os.environ.get("GLM_API_KEY", "")
    GLM_API_BASE: str = os.environ.get("GLM_API_BASE", "https://coding.dashscope.aliyuncs.com/v1")
    GLM_MODEL: str = os.environ.get("GLM_MODEL", "glm-5")
    
    # OpenAI 兼容配置（CrewAI 需要）
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "sk-dummy-key-for-crewai")
    
    # ========== LLM 参数 ==========
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096
    
    # ========== 数据源配置 ==========
    # Qlib 数据路径
    QLIB_DATA_PATH: str = os.environ.get("QLIB_DATA_PATH", "~/.qlib/qlib_data/cn_data")
    
    # ========== API 配置 ==========
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # ========== 日志配置 ==========
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否完整"""
        errors = []
        
        if not cls.GLM_API_KEY:
            errors.append("GLM_API_KEY 未设置")
        
        if errors:
            print("⚠️ 配置验证失败:")
            for err in errors:
                print(f"  - {err}")
            print("\n请创建 .env 文件或设置环境变量:")
            print("  GLM_API_KEY=你的智谱AI密钥")
            return False
        
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """获取 LLM 配置字典"""
        return {
            "model": cls.GLM_MODEL,
            "api_base": cls.GLM_API_BASE,
            "api_key": cls.GLM_API_KEY,
            "temperature": cls.LLM_TEMPERATURE,
        }


# 模块级单例
config = Config()


if __name__ == "__main__":
    # 测试配置
    print("=== 配置检查 ===")
    print(f"GLM_API_KEY: {'已设置' if config.GLM_API_KEY else '❌ 未设置'}")
    print(f"GLM_API_BASE: {config.GLM_API_BASE}")
    print(f"GLM_MODEL: {config.GLM_MODEL}")
    print()
    config.validate()