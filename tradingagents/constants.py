#!/usr/bin/env python3
"""
全局常量定义
集中管理所有magic numbers和配置常量
"""

# ==================== 全局常量 ====================
DEFAULT_OUTPUT_LANGUAGE = "zh"

# ==================== 置信度常量 ====================
STRONG_CONFIDENCE = 0.75
WEAK_CONFIDENCE = 0.55
NEUTRAL_CONFIDENCE = 0.65

# ==================== 胜率常量 ====================
DEFAULT_BULL_WIN_RATE = 0.52
DEFAULT_BEAR_WIN_RATE = 0.48
DEFAULT_NEUTRAL_WIN_RATE = 0.50

# ==================== RSI阈值 ====================
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ==================== 重试配置 ====================
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2
RETRY_BACKOFF_MULTIPLIER = 2

# ==================== 辩论间隔 ====================
# 研究员辩论每轮发言后的等待时间（秒），避免 API 限速
# 设为 0 可取消等待，加快辩论速度
RESEARCHER_DEBATE_SLEEP_SECONDS = 1

# ==================== 缓存配置 ====================
CACHE_TTL_HOURS = 24
MAX_CACHE_SIZE = 1000

# ==================== LLM配置 ====================
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 2000
LLM_TIMEOUT_SECONDS = 30

# ==================== 辩论配置 ====================
MAX_DEBATE_ROUNDS = 2
MAX_RISK_DISCUSS_ROUNDS = 2
MAX_RECUR_LIMIT = 100

# ==================== 指标周期 ====================
SMA_PERIODS = [5, 10, 20, 50, 100, 200]
EMA_PERIODS = [5, 10, 20, 50, 100, 200]
VOLUME_SMA_PERIODS = [5, 10, 20, 50]

# ==================== 技术指标参数 ====================
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

RSI_PERIOD = 14
ATR_PERIOD = 14
ADX_PERIOD = 14
CMO_PERIOD = 14
MFI_PERIOD = 14

BOLLINGER_PERIOD = 20
BOLLINGER_STD_MULTIPLIER = 2.0

VWMA_PERIOD = 20

# ==================== 数据回看天数 ====================
DEFAULT_LOOKBACK_DAYS = 120
MIN_REQUIRED_DATA_POINTS = 50

# ==================== 日志配置 ====================
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

# ==================== 数据库配置 ====================
DEFAULT_DB_PATH = "tradingagents/db/research_tracker.db"
DEFAULT_ANALYSIS_DB_PATH = "tradingagents/db/trading_analysis.db"
DB_TIMEOUT_SECONDS = 30

# ==================== 日志文件路径 ====================
TOOL_CALL_LOG_PATH = "langgraph_outputs/tool_calls.log"

# ==================== API配置 ====================
API_REQUEST_TIMEOUT = 30
API_MAX_RETRIES = 3

# ==================== 分析师配置 ====================
ANALYST_TYPES = ["market", "sentiment", "news", "fundamentals", "candlestick"]
RISK_ANALYST_TYPES = ["moderate", "aggressive"]

# ==================== Researcher 注册表 ====================
# 所有可用的 researcher 定义
# key: researcher 简称（用于配置选择）
# value: {
#   "type": researcher_type（用于内部标识和 memory key）
#   "display_name": 图节点显示名称
#   "speaker_label": 在辩论中的发言标签
#   "module": 工厂模块路径
#   "factory": 工厂函数名
#   "default_win_rate": 默认胜率
# }
RESEARCHER_REGISTRY = {
    "bull": {
        "type": "bull_researcher",
        "display_name": "Bull Researcher",
        "speaker_label": "Bull",
        "module": "tradingagents.agents.researchers.bull_researcher",
        "factory": "create_bull_researcher",
        "default_win_rate": DEFAULT_BULL_WIN_RATE,
    },
    "bear": {
        "type": "bear_researcher",
        "display_name": "Bear Researcher",
        "speaker_label": "Bear",
        "module": "tradingagents.agents.researchers.bear_researcher",
        "factory": "create_bear_researcher",
        "default_win_rate": DEFAULT_BEAR_WIN_RATE,
    },
    "buffett": {
        "type": "buffett_researcher",
        "display_name": "Buffett Researcher",
        "speaker_label": "Buffett",
        "module": "tradingagents.agents.researchers.buffett_researcher",
        "factory": "create_buffett_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "cathie_wood": {
        "type": "cathie_wood_researcher",
        "display_name": "Cathie Wood Researcher",
        "speaker_label": "CathieWood",
        "module": "tradingagents.agents.researchers.cathie_wood_researcher",
        "factory": "create_cathie_wood_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "peter_lynch": {
        "type": "peter_lynch_researcher",
        "display_name": "Peter Lynch Researcher",
        "speaker_label": "PeterLynch",
        "module": "tradingagents.agents.researchers.peter_lynch_researcher",
        "factory": "create_peter_lynch_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "charlie_munger": {
        "type": "charlie_munger_researcher",
        "display_name": "Charlie Munger Researcher",
        "speaker_label": "Munger",
        "module": "tradingagents.agents.researchers.charlie_munger_researcher",
        "factory": "create_charlie_munger_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "soros": {
        "type": "soros_researcher",
        "display_name": "Soros Researcher",
        "speaker_label": "Soros",
        "module": "tradingagents.agents.researchers.soros_researcher",
        "factory": "create_soros_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "dalio": {
        "type": "dalio_researcher",
        "display_name": "Dalio Researcher",
        "speaker_label": "Dalio",
        "module": "tradingagents.agents.researchers.dalio_researcher",
        "factory": "create_dalio_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
    "livermore": {
        "type": "livermore_researcher",
        "display_name": "Livermore Researcher",
        "speaker_label": "Livermore",
        "module": "tradingagents.agents.researchers.livermore_researcher",
        "factory": "create_livermore_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
}

# 默认选中的 researcher
# 三方辩论：Bull（看多初阶）+ Bear（看空初阶）+ Buffett（价值锚定高级）
#
# 分析师层级体系：
# - 初阶分析师（Junior）：bull, bear — 预设立场，快速多空筛选
# - 高级分析师（Senior/Master）：buffett, cathie_wood, peter_lynch,
#   charlie_munger, soros, dalio, livermore — 无预设立场，独立判断
#
# 设计依据（基于回测数据分析）：
# 1. 双方辩论(bull+bear)导致 Research Manager 90% 给出 HOLD，错过 INTC +5.7%、IREN +7.3% 等机会
# 2. Buffett 的价值锚定视角（护城河/安全边际/FCF）与 Bull/Bear 的技术面+情绪面互补性最强
# 3. 三人辩论 2 轮 = 6 次发言 ≈ 25k tokens，在 LLM context 可控范围内
# 4. 加更多大师会导致 context 膨胀（5人=42k tokens），Research Manager 注意力涣散反而更保守
# 5. Cathie Wood / Peter Lynch 与 Bull 视角重叠度高，增加噪声 > 信号
#
# 推荐组合：
# - 默认组合：["bull", "bear", "buffett"] — 经典多空+价值锚定
# - 大师组合：["buffett", "charlie_munger", "soros"] — 价值+逆向+宏观
# - 全面组合：["bull", "bear", "buffett", "soros", "dalio"] — 5人深度辩论（token 消耗较高）
DEFAULT_SELECTED_RESEARCHERS = ["bull", "bear", "buffett"]

# 向后兼容旧字段名
RESEARCHER_TYPES = list(RESEARCHER_REGISTRY.keys())

# ==================== 支撑/压力位窗口 ====================
SUPPORT_RESISTANCE_WINDOW_20 = 20
SUPPORT_RESISTANCE_WINDOW_50 = 50

# ==================== 波动率计算 ====================
VOLATILITY_WINDOW_20 = 20
VOLATILITY_WINDOW_50 = 50
TRADING_DAYS_PER_YEAR = 252

# ==================== 趋势线计算窗口 ====================
TREND_SLOPE_WINDOW_10 = 10
TREND_SLOPE_WINDOW_20 = 20

LINEAR_REGRESSION_WINDOW_20 = 20

# ==================== ROC周期 ====================
ROC_PERIODS = [5, 10, 20]

# ==================== CCI配置 ====================
CCI_PERIOD = 20
CCI_CONSTANT = 0.015

# ==================== 背离检测窗口 ====================
DIVERGENCE_WINDOW = 20

# ==================== 蜡烛图形态检测窗口 ====================
PATTERN_LOOKBACK = 60
PEAK_TROUGH_WINDOW = 5

# ==================== 图表形态阈值 ====================
# 头肩顶/底：两肩高度差阈值（5%）
HEAD_SHOULDERS_TOLERANCE = 0.05
# 双顶/双底：两峰/谷差阈值（3%）
DOUBLE_TOP_BOTTOM_TOLERANCE = 0.03
# 三角形/矩形：水平线容差阈值（2%）
TRIANGLE_FLAT_TOLERANCE = 0.02
# 旗形：趋势要求（前半段涨跌幅 > 5%）
FLAG_TREND_THRESHOLD = 0.05
# 旗形：整理区间振幅上限（3%）
FLAG_RANGE_THRESHOLD = 0.03

# ==================== 预测验证阈值 ====================
# 用于判断预测是否正确的价格变动阈值（2%）
PREDICTION_THRESHOLD = 0.02

# ==================== 回测配置 ====================
# 回测默认初始资金（美元）
DEFAULT_INITIAL_CAPITAL = 10000.0

# ==================== 数据窗口 ====================
# 股票数据最小天数窗口（用于技术指标计算所需的历史数据量）
MIN_STOCK_DATA_DAYS = 200

# ==================== 交易信号 ====================
SIGNAL_BULLISH = 1
SIGNAL_BEARISH = -1
SIGNAL_NEUTRAL = 0
