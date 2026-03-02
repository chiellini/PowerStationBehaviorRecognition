"""
电力高压柜安全操作视频分析系统配置
"""
from pathlib import Path
import os

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    # 加载项目根目录的 .env 文件
    PROJECT_ROOT = Path(__file__).parent.parent
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # 尝试加载 configs/.env
        configs_env_path = PROJECT_ROOT / "configs" / ".env"
        if configs_env_path.exists():
            load_dotenv(dotenv_path=configs_env_path)
except ImportError:
    pass

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
VIDEO_DIR = PROJECT_ROOT / "sources_video"
OUTPUT_DIR = PROJECT_ROOT / "output"

# API 配置
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# 支持的模型（只支持 Kimi 多模态，性价比高）
AVAILABLE_MODELS = {
    "kimi": "moonshotai/kimi-k2.5",           # 推荐：Kimi K2.5（默认）
    "kimi-vision": "moonshotai/kimi-vision",  # Kimi 视觉增强版
}

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", AVAILABLE_MODELS["kimi"])
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "80"))
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "300"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# 支持的视频格式
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mpeg", ".mpg", ".m4v", ".avi"}

# PPE（个人防护装备）配置
PPE_ITEMS = {
    "helmet": {"name": "安全头盔", "required": True},
    "insulating_clothing": {"name": "绝缘服", "required": True},
    "insulating_gloves": {"name": "绝缘手套", "required": True},
}

# 动作类型配置
ACTION_TYPES = {
    "pick": "捡起",
    "insert": "插入",
    "rotate": "旋转",
    "place": "放置",
    "open": "打开",
    "close": "关闭",
    "toggle": "拨动",
    "hang": "悬挂",
    "lock": "锁定",
    "press": "按压",
}

# 方向配置
DIRECTIONS = {
    "clockwise": "顺时针",
    "counter_clockwise": "逆时针",
}