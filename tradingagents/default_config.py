import os
from .constants import (
    MAX_DEBATE_ROUNDS,
    MAX_RISK_DISCUSS_ROUNDS,
    MAX_RECUR_LIMIT,
    DEFAULT_OUTPUT_LANGUAGE,
    CACHE_TTL_HOURS,
    DEFAULT_SELECTED_RESEARCHERS,
)

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings - 使用 OpenCode Zen (Minimax/GLM)
    "llm_provider": "openai",
    "deep_think_llm": "minimax-m2.5-free",
    "quick_think_llm": "minimax-m2.5-free",
    "backend_url": "https://opencode.ai/zen/v1",
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    # Debate and discussion settings
    "max_debate_rounds": MAX_DEBATE_ROUNDS,
    "max_risk_discuss_rounds": MAX_RISK_DISCUSS_ROUNDS,
    "max_recur_limit": MAX_RECUR_LIMIT,
    # Researcher selection - 选择参与辩论的研究员
    # 初阶（Junior）: "bull", "bear" — 预设立场，快速多空筛选
    # 高级（Senior）: "buffett", "cathie_wood", "peter_lynch",
    #                  "charlie_munger", "soros", "dalio", "livermore"
    # 默认: ["bull", "bear", "buffett"]（初阶多空 + 价值锚定）
    # 示例: ["buffett", "charlie_munger", "soros"]（大师组合：价值+逆向+宏观）
    # 示例: ["bull", "bear", "buffett", "soros", "dalio"]（5人深度辩论，token消耗较高）
    "selected_researchers": DEFAULT_SELECTED_RESEARCHERS,
    # Language configuration - 输出语言设置
    # Options: "zh" (中文), "en" (English), "auto" (自动检测)
    "output_language": DEFAULT_OUTPUT_LANGUAGE,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "longbridge",     # Options: alpha_vantage, yfinance, longbridge
        "technical_indicators": "longbridge",# Options: alpha_vantage, yfinance, longbridge
        "fundamental_data": "longbridge",    # Options: alpha_vantage, yfinance, longbridge
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance, longbridge
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_stock_data": "longbridge",      # 使用长桥API
    },
    # Debug settings
    "debug": {
        "enabled": True,  # 调试模式开关
        "verbose": True,  # 详细日志
        "show_prompts": True,  # 显示完整prompt
        "log_level": "INFO",  # 日志级别: DEBUG, INFO, WARNING, ERROR
    },
    # Backtest settings
    "backtest": {
        "enabled": True,  # 是否开启回测功能
    },
    # Cache settings
    "cache": {
        "ttl_hours": CACHE_TTL_HOURS,  # 默认缓存时长（小时）
    },
}
