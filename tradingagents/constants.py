"""
TradingAgents 全局常量定义

包含置信度、胜率、重试策略等魔术数字的统一定义。
使用常量提高代码可维护性和可读性。
"""

# ==================== 置信度常量 ====================

# 强信号置信度阈值 (>= 75%)
STRONG_CONFIDENCE = 0.75

# 中等信号置信度阈值 (>= 65%)
MODERATE_CONFIDENCE = 0.65

# 弱信号置信度阈值 (>= 55%)
WEAK_CONFIDENCE = 0.55

# 中性/无法判断置信度
NEUTRAL_CONFIDENCE = 0.50


# ==================== 胜率常量 ====================

# 默认牛市研究员历史胜率
DEFAULT_BULL_WIN_RATE = 0.52

# 默认熊市研究员历史胜率
DEFAULT_BEAR_WIN_RATE = 0.48

# 高胜率阈值（显示为"优秀"）
HIGH_WIN_RATE_THRESHOLD = 0.60

# 低胜率阈值（显示为"需改进"）
LOW_WIN_RATE_THRESHOLD = 0.45


# ==================== 重试策略常量 ====================

# 最大重试次数（API调用失败时）
MAX_RETRY_ATTEMPTS = 3

# 重试基础延迟（秒）- 使用指数退避
RETRY_BASE_DELAY = 1.0

# 重试最大延迟（秒）
RETRY_MAX_DELAY = 10.0


# ==================== 缓存策略常量 ====================

# 数据缓存默认TTL（小时）
CACHE_TTL_HOURS = 24

# 股票数据缓存TTL（小时）- 交易日数据24小时有效
STOCK_DATA_CACHE_TTL_HOURS = 24

# 新闻数据缓存TTL（小时）- 新闻更新频繁，缓存6小时
NEWS_CACHE_TTL_HOURS = 6

# 基本面数据缓存TTL（小时）- 季度数据，缓存7天
FUNDAMENTALS_CACHE_TTL_HOURS = 168  # 7 * 24


# ==================== 数据获取常量 ====================

# 默认回看天数（技术分析）
DEFAULT_LOOKBACK_DAYS = 90

# 最小回看天数
MIN_LOOKBACK_DAYS = 30

# 最大回看天数
MAX_LOOKBACK_DAYS = 365

# 技术指标计算所需最小数据点数
MIN_DATA_POINTS_FOR_INDICATORS = 50


# ==================== LLM配置常量 ====================

# LLM调用最大重试次数
LLM_MAX_RETRIES = 3

# LLM调用超时（秒）
LLM_TIMEOUT_SECONDS = 120

# LLM输出最大token数（默认）
LLM_MAX_OUTPUT_TOKENS = 4096


# ==================== 辩论和讨论常量 ====================

# 最大辩论轮数（Bull vs Bear）
MAX_DEBATE_ROUNDS = 2

# 最大风险讨论轮数
MAX_RISK_DISCUSS_ROUNDS = 2

# 最大递归深度限制
MAX_RECUR_LIMIT = 100


# ==================== 预测关键词 ====================

# 看涨关键词列表
BULLISH_KEYWORDS = [
    "buy", "bull", "bullish", "long", "upward", "uptrend", 
    "positive", "growth", "increase", "rise", "买入", "看涨", "做多"
]

# 看跌关键词列表
BEARISH_KEYWORDS = [
    "sell", "bear", "bearish", "short", "downward", "downtrend",
    "negative", "decline", "decrease", "fall", "卖出", "看跌", "做空"
]

# 持有关键词列表
HOLD_KEYWORDS = [
    "hold", "neutral", "wait", "观望", "持有", "中性"
]


# ==================== 数据验证常量 ====================

# 股票代码最大长度
MAX_SYMBOL_LENGTH = 10

# 股票代码最小长度
MIN_SYMBOL_LENGTH = 1

# 日期格式
DATE_FORMAT = "%Y-%m-%d"

# 允许的股票代码字符集（字母、数字、点、连字符）
VALID_SYMBOL_CHARS = r'^[A-Za-z0-9\.\-]+$'


# ==================== 数据库常量 ====================

# 回测数据库名称
BACKTEST_DB_NAME = "backtest.db"

# 预测记录保留天数
PREDICTION_RETENTION_DAYS = 365


# ==================== 文件路径常量 ====================

# 数据缓存目录名
DATA_CACHE_DIR = "data_cache"

# 结果输出目录名
RESULTS_DIR = "results"

# 报告目录名
REPORTS_DIR = "reports"


# ==================== 其他常量 ====================

# 支持的输出语言
SUPPORTED_LANGUAGES = ["zh", "en", "auto"]

# 默认输出语言
DEFAULT_OUTPUT_LANGUAGE = "zh"

# 支持的LLM提供商
SUPPORTED_LLM_PROVIDERS = ["openai", "anthropic", "google", "xai", "ollama"]
