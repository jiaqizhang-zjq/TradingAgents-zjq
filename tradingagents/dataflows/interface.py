from typing import Annotated
import pandas as pd
import io

# Import from vendor-specific modules
from .y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
    get_fundamentals as get_yfinance_fundamentals,
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .yfinance_news import get_news_yfinance, get_global_news_yfinance
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news,
)

# 长桥API模块（默认选项）
from .longbridge import (
    get_stock as get_longbridge_stock,
    get_indicator as get_longbridge_indicator,
    get_fundamentals as get_longbridge_fundamentals,
    get_balance_sheet as get_longbridge_balance_sheet,
    get_cashflow as get_longbridge_cashflow,
    get_income_statement as get_longbridge_income_statement,
    get_insider_transactions as get_longbridge_insider_transactions,
    get_news as get_longbridge_news,
    get_global_news as get_longbridge_global_news,
    get_candlestick_patterns as get_longbridge_candlestick_patterns,
)

# 导入本地计算模块
from .complete_indicators import (
    CompleteTechnicalIndicators,
    CompleteCandlestickPatterns,
    ChartPatterns
)

# 导入统一数据管理器
from .unified_data_manager import (
    UnifiedDataManager,
    VendorPriority,
    DataFetchError,
)

# Configuration and routing logic
from .config import get_config

# 全局统一数据管理器实例
_data_manager: UnifiedDataManager = None

# ========== LOCAL VENDOR 实现 ==========
def _parse_stock_data(stock_data_str):
    """解析股票数据字符串为DataFrame"""
    try:
        # 尝试解析CSV格式 (timestamp,open,high,low,close,volume,adjusted_close)
        if 'timestamp' in stock_data_str and 'open' in stock_data_str and 'high' in stock_data_str:
            df = pd.read_csv(io.StringIO(stock_data_str))
            
            if 'timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('Date')
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col.capitalize()] = pd.to_numeric(df[col], errors='coerce')
                        df = df.drop(columns=[col])
                
                return df
        
        # 尝试解析表格格式 (| Date | Open | ... |)
        if 'Date' in stock_data_str and 'Open' in stock_data_str:
            lines = stock_data_str.strip().split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('|-') and line.strip()]
            cleaned_data = '\n'.join(filtered_lines)
            
            df = pd.read_csv(io.StringIO(cleaned_data), sep='\\s*\\|\\s*', engine='python')
            
            df.columns = [col.strip() for col in df.columns if col.strip()]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
    except Exception as e:
        print(f"[_parse_stock_data] Error: {e}")
        import traceback
        print(f"[_parse_stock_data] Traceback:\n{traceback.format_exc()}")
        pass
    return None

def _local_get_indicators(symbol, indicator, curr_date, look_back_days, *args, **kwargs):
    """本地计算技术指标（使用惰性计算优化）"""
    from datetime import datetime, timedelta
    from .lazy_indicators import get_lazy_calculator
    from .indicator_groups import get_indicator_columns
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        end_date = curr_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df.reset_index(inplace=True)
    
    # 准备干净的 DataFrame（避免不必要的复制）
    df_clean = df.rename(columns={
        'timestamp': 'timestamp',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # 使用惰性计算器 - 只计算需要的指标
    lazy_calc = get_lazy_calculator(df_clean)
    
    # 获取该指标组需要的列
    all_columns = BASE_COLUMNS + lazy_calc.get_available_indicators()
    needed_indicators = get_indicator_columns(indicator, all_columns)
    
    # 只计算需要的指标（不是全部100+个）
    needed_indicators = [col for col in needed_indicators if col not in BASE_COLUMNS]
    result_df = lazy_calc.get_indicators(needed_indicators)
    
    # 只返回最近需要的天数
    result_df = result_df.tail(look_back_days + 10)
    
    return result_df.to_csv(index=False)


def _ensure_stock_data(symbol: str, curr_date: str, look_back_days: int, stock_data: str = '') -> str:
    """确保有股票数据，如果没有则获取"""
    if stock_data:
        return stock_data
    
    from datetime import datetime, timedelta
    manager = get_data_manager()
    end_date = curr_date
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
    return manager.fetch("get_stock_data", symbol, start_date, end_date)


def _prepare_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """准备干净的DataFrame用于指标计算"""
    df.reset_index(inplace=True)
    
    # 优化：避免创建新 DataFrame，使用 rename
    df_clean = df.rename(columns={
        'timestamp': 'timestamp',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    return df_clean


def _collect_all_needed_indicators() -> set:
    """收集所有分组需要的指标（去重）"""
    from .indicator_groups import INDICATOR_GROUPS, BASE_COLUMNS
    
    all_needed_indicators = set()
    for group_name, indicators in INDICATOR_GROUPS.items():
        for ind in indicators:
            if ind not in BASE_COLUMNS:
                all_needed_indicators.add(ind)
    return all_needed_indicators


def _build_grouped_results(df_with_indicators: pd.DataFrame, look_back_days: int) -> dict:
    """按分组构建结果字典"""
    from .indicator_groups import INDICATOR_GROUPS
    
    result = {}
    for group_name, indicators in INDICATOR_GROUPS.items():
        group_df = df_with_indicators[[col for col in indicators if col in df_with_indicators.columns]]
        group_df = group_df.tail(look_back_days + 10)
        result[group_name] = group_df.to_csv(index=False)
    return result


def _local_get_all_indicators(symbol, curr_date, look_back_days, stock_data='', *args, **kwargs):
    """本地计算所有技术指标，一次性返回所有分组（使用惰性计算优化）"""
    from .lazy_indicators import get_lazy_calculator
    import traceback
    
    try:
        print(f"[_local_get_all_indicators] symbol={symbol}, curr_date={curr_date}, look_back_days={look_back_days}")
        print(f"[_local_get_all_indicators] stock_data length={len(stock_data) if stock_data else 0}")
        
        # 1. 确保有股票数据
        stock_data = _ensure_stock_data(symbol, curr_date, look_back_days, stock_data)
        
        # 2. 解析并验证数据
        df = _parse_stock_data(stock_data)
        if df is None:
            raise DataFetchError("Failed to parse stock data")
        print(f"[_local_get_all_indicators] df parsed, shape={df.shape}")
        
        # 3. 准备干净的 DataFrame
        df_clean = _prepare_clean_dataframe(df)
        print(f"[_local_get_all_indicators] df_clean shape={df_clean.shape}")
        
        # 4. 收集所有需要的指标
        all_needed_indicators = _collect_all_needed_indicators()
        print(f"[_local_get_all_indicators] calculating {len(all_needed_indicators)} unique indicators...")
        
        # 5. 批量计算指标
        lazy_calc = get_lazy_calculator(df_clean)
        df_with_indicators = lazy_calc.get_indicators(list(all_needed_indicators))
        
        # 6. 构建分组结果
        print(f"[_local_get_all_indicators] building result groups...")
        result = _build_grouped_results(df_with_indicators, look_back_days)
        
        print(f"[_local_get_all_indicators] done, result has {len(result)} groups")
        return result
        
    except Exception as e:
        print(f"[_local_get_all_indicators] ERROR: {e}")
        print(f"[_local_get_all_indicators] Traceback:\n{traceback.format_exc()}")
        raise DataFetchError(f"_local_get_all_indicators failed: {e}")

def _local_get_candlestick_patterns(symbol, start_date, end_date, *args, **kwargs):
    """本地识别蜡烛图形态"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df.reset_index(inplace=True)
    
    df_clean = pd.DataFrame()
    df_clean['timestamp'] = df['timestamp']
    df_clean['open'] = df['Open']
    df_clean['high'] = df['High']
    df_clean['low'] = df['Low']
    df_clean['close'] = df['Close']
    df_clean['volume'] = df['Volume']
    
    result_df = CompleteCandlestickPatterns.identify_patterns(df_clean)
    
    if len(result_df) == 0:
        return f"No candlestick patterns identified for {symbol} in the date range {start_date} to {end_date}"
    
    patterns_result = []
    for _, row in result_df.iterrows():
        date_str = row.get('timestamp', '')
        patterns_str = row.get('patterns', '')
        volume_confirmed = row.get('volume_confirmed', False)
        
        if volume_confirmed and patterns_str:
            patterns_list = patterns_str.split('|')
            patterns_with_confirmation = [f"{p}(VOL_CONFIRMED)" for p in patterns_list]
            patterns_str = '|'.join(patterns_with_confirmation)
        elif volume_confirmed:
            patterns_str = "(VOL_CONFIRMED)"
        
        patterns_result.append({
            'Date': date_str,
            'Patterns': patterns_str.replace('|', ', '),
            'Open': round(row.get('open', 0), 2),
            'High': round(row.get('high', 0), 2),
            'Low': round(row.get('low', 0), 2),
            'Close': round(row.get('close', 0), 2)
        })
    
    result = f"# Candlestick Patterns for {symbol} ({start_date} to {end_date})\n\n"
    result += "| Date       | Patterns                                      | Open   | High   | Low    | Close  |\n"
    result += "|------------|-----------------------------------------------|--------|--------|--------|--------|\n"
    
    for p in patterns_result:
        patterns_str = p['Patterns']
        if len(patterns_str) > 45:
            patterns_str = patterns_str[:42] + "..."
        result += f"| {p['Date']} | {patterns_str:<45} | {p['Open']:>6} | {p['High']:>6} | {p['Low']:>6} | {p['Close']:>6} |\n"
    
    all_patterns = []
    for p in patterns_result:
        all_patterns.extend(p['Patterns'].split(', '))
    
    pattern_counts = {}
    for pat in all_patterns:
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
    
    result += f"\n## Pattern Summary\n"
    result += "| Pattern                | Count |\n"
    result += "|------------------------|-------|\n"
    for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        result += f"| {pat:<22} | {cnt:>5} |\n"
    
    return result

def _local_get_chart_patterns(symbol, start_date, end_date, lookback=60, *args, **kwargs):
    """本地识别西方图表形态"""
    from datetime import datetime, timedelta
    import traceback
    
    try:
        print(f"[_local_get_chart_patterns] symbol={symbol}, start_date={start_date}, end_date={end_date}")
        
        stock_data = kwargs.get('stock_data', '')
        manager = get_data_manager()
        
        if not stock_data:
            print(f"[_local_get_chart_patterns] fetching stock data...")
            stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
        
        print(f"[_local_get_chart_patterns] parsing stock data...")
        df = _parse_stock_data(stock_data)
        
        if df is None:
            raise DataFetchError("Failed to parse stock data")
        
        print(f"[_local_get_chart_patterns] df parsed, shape={df.shape}")
        print(f"[_local_get_chart_patterns] df columns={list(df.columns)}")
        
        df.reset_index(inplace=True)
        
        # 优化：直接 rename 而不是创建新 DataFrame
        df_clean = df.rename(columns={
            'timestamp': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        print(f"[_local_get_chart_patterns] calling identify_all_patterns...")
        patterns = ChartPatterns.identify_all_patterns(df_clean, lookback)
        print(f"[_local_get_chart_patterns] identify_all_patterns done")
        
        result_lines = [
            f"# Chart Patterns for {symbol}",
            "",
            "| Pattern Type | Detected | Confidence | Volume Confirmed | Breakout Confirmed | Description |",
            "|--------------|----------|------------|------------------|-------------------|-------------|"
        ]
        
        for pattern_name, pattern_info in patterns.items():
            detected = "✅" if pattern_info.get("detected", False) else "❌"
            confidence = f"{pattern_info.get('confidence', 0):.2%}"
            volume_confirmed = "✅" if pattern_info.get("volume_confirmed", False) else "❌"
            breakout_confirmed = "✅" if pattern_info.get("breakout_confirmed", False) else "❌"
            description = pattern_info.get("description", "")
            result_lines.append(f"| {pattern_name:<12} | {detected:<8} | {confidence:<10} | {volume_confirmed:<16} | {breakout_confirmed:<17} | {description} |")
        
        result_lines.extend(["", "## Detailed Pattern Information", ""])
        for pattern_name, pattern_info in patterns.items():
            if pattern_info.get("detected", False):
                result_lines.append(f"### {pattern_name}")
                for key, value in pattern_info.items():
                    if key not in ["detected", "description"]:
                        result_lines.append(f"- {key}: {value}")
                result_lines.append("")
        
        return "\n".join(result_lines)
    except Exception as e:
        print(f"[_local_get_chart_patterns] ERROR: {e}")
        print(f"[_local_get_chart_patterns] Traceback:\n{traceback.format_exc()}")
        raise DataFetchError(f"_local_get_chart_patterns failed: {e}")

# ========== 数据管理器初始化 ==========
def get_data_manager() -> UnifiedDataManager:
    """获取全局数据管理器实例"""
    global _data_manager
    
    if _data_manager is None:
        _data_manager = _init_data_manager()
    
    return _data_manager

def _init_data_manager() -> UnifiedDataManager:
    """初始化数据管理器"""
    manager = UnifiedDataManager(
        default_max_retries=3,
        default_retry_delay_base=1.0,
        default_retry_delay_max=10.0,
        default_rate_limit_wait=5.0,
        default_rate_limit_max_retries=5,
    )
    
    config = get_config()
    
    manager.register_vendor(
        "local",
        priority=VendorPriority.PRIMARY,
        max_retries=1,
        rate_limit_wait=0.0,
    )
    
    manager.register_vendor(
        "longbridge",
        priority=VendorPriority.SECONDARY,
        max_retries=3,
        rate_limit_wait=2.0,
    )
    
    manager.register_vendor(
        "yfinance",
        priority=VendorPriority.FALLBACK,
        max_retries=3,
        rate_limit_wait=1.0,
    )
    
    manager.register_vendor(
        "alpha_vantage",
        priority=VendorPriority.FALLBACK,
        max_retries=2,
        rate_limit_wait=12.0,
    )
    
    get_stock_data_impls = {}
    get_stock_data_impls["longbridge"] = get_longbridge_stock
    get_stock_data_impls["yfinance"] = get_YFin_data_online
    get_stock_data_impls["alpha_vantage"] = get_alpha_vantage_stock
    
    manager.register_method(
        "get_stock_data",
        get_stock_data_impls,
        ["longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_indicators_impls = {}
    get_indicators_impls["local"] = _local_get_indicators
    get_indicators_impls["longbridge"] = get_longbridge_indicator
    get_indicators_impls["yfinance"] = get_stock_stats_indicators_window
    get_indicators_impls["alpha_vantage"] = get_alpha_vantage_indicator
    
    manager.register_method(
        "get_indicators",
        get_indicators_impls,
        ["local", "longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_all_indicators_impls = {}
    get_all_indicators_impls["local"] = _local_get_all_indicators
    
    manager.register_method(
        "get_all_indicators",
        get_all_indicators_impls,
        ["local"]
    )
    
    get_fundamentals_impls = {}
    get_fundamentals_impls["longbridge"] = get_longbridge_fundamentals
    get_fundamentals_impls["yfinance"] = get_yfinance_fundamentals
    get_fundamentals_impls["alpha_vantage"] = get_alpha_vantage_fundamentals
    
    manager.register_method(
        "get_fundamentals",
        get_fundamentals_impls,
        ["longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_balance_sheet_impls = {}
    get_balance_sheet_impls["alpha_vantage"] = get_alpha_vantage_balance_sheet
    get_balance_sheet_impls["yfinance"] = get_yfinance_balance_sheet
    get_balance_sheet_impls["longbridge"] = get_longbridge_balance_sheet
    
    manager.register_method(
        "get_balance_sheet",
        get_balance_sheet_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_cashflow_impls = {}
    get_cashflow_impls["alpha_vantage"] = get_alpha_vantage_cashflow
    get_cashflow_impls["yfinance"] = get_yfinance_cashflow
    get_cashflow_impls["longbridge"] = get_longbridge_cashflow
    
    manager.register_method(
        "get_cashflow",
        get_cashflow_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_income_statement_impls = {}
    get_income_statement_impls["alpha_vantage"] = get_alpha_vantage_income_statement
    get_income_statement_impls["yfinance"] = get_yfinance_income_statement
    get_income_statement_impls["longbridge"] = get_longbridge_income_statement
    
    manager.register_method(
        "get_income_statement",
        get_income_statement_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_news_impls = {}
    get_news_impls["alpha_vantage"] = get_alpha_vantage_news
    get_news_impls["yfinance"] = get_news_yfinance
    
    manager.register_method(
        "get_news",
        get_news_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    get_global_news_impls = {}
    get_global_news_impls["alpha_vantage"] = get_alpha_vantage_global_news
    get_global_news_impls["yfinance"] = get_global_news_yfinance
    
    manager.register_method(
        "get_global_news",
        get_global_news_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    get_insider_transactions_impls = {}
    get_insider_transactions_impls["alpha_vantage"] = get_alpha_vantage_insider_transactions
    get_insider_transactions_impls["yfinance"] = get_yfinance_insider_transactions
    
    manager.register_method(
        "get_insider_transactions",
        get_insider_transactions_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    # 蜡烛图形态工具
    get_candlestick_patterns_impls = {}
    get_candlestick_patterns_impls["local"] = _local_get_candlestick_patterns
    get_candlestick_patterns_impls["longbridge"] = get_longbridge_candlestick_patterns
    
    manager.register_method(
        "get_candlestick_patterns",
        get_candlestick_patterns_impls,
        ["local", "longbridge"]
    )
    
    # 西方图表形态工具
    get_chart_patterns_impls = {}
    get_chart_patterns_impls["local"] = _local_get_chart_patterns
    
    manager.register_method(
        "get_chart_patterns",
        get_chart_patterns_impls,
        ["local"]
    )
    
    return manager

def route_to_vendor(method: str, *args, **kwargs):
    """路由方法调用到统一数据管理器
    
    这是兼容旧代码的接口，新代码应该直接使用 get_data_manager()
    
    Args:
        method: 方法名称
        *args: 位置参数
        **kwargs: 关键字参数
    
    Returns:
        获取的数据
    """
    from datetime import datetime, timedelta
    
    manager = get_data_manager()
    
    if method == "get_stock_data":
        args_list = list(args)
        if len(args_list) >= 3:
            symbol, start_date, end_date = args_list[:3]
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                days_diff = (end_dt - start_dt).days
                
                if days_diff < 200:
                    new_start_dt = end_dt - timedelta(days=200)
                    new_start_date = new_start_dt.strftime("%Y-%m-%d")
                    args_list[1] = new_start_date
                    args = tuple(args_list)
            except Exception:
                pass
    
    return manager.fetch(method, *args, **kwargs)

def get_fetch_stats():
    """获取数据获取统计信息"""
    manager = get_data_manager()
    return manager.get_stats()

def reset_fetch_stats():
    """重置数据获取统计信息"""
    manager = get_data_manager()
    manager.reset_stats()
