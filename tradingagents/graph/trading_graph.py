# TradingAgents/graph/trading_graph.py (重构后简化版)

import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from langgraph.prebuilt import ToolNode

from tradingagents.llm_clients import create_llm_client
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)

from tradingagents.agents.backtest import run_backtest
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config
from tradingagents.constants import RESEARCHER_REGISTRY, DEFAULT_SELECTED_RESEARCHERS
from .helpers import StatePersistence

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_transactions,
    get_global_news
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=None,
        debug=False,
        config: Dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include.
                Defaults to ["market", "social", "news", "fundamentals", "candlestick"].
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
            callbacks: Optional list of callback handlers (e.g., for tracking LLM/tool stats)
        """
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals", "candlestick"]
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.callbacks = callbacks or []
        
        # 初始化持久化管理器
        self.persistence = StatePersistence(debug=debug)

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # 初始化LLMs，使用提供商特定的思考配置
        llm_kwargs = self._get_provider_kwargs()

        # 如果提供了回调，则添加到kwargs中（传递给LLM构造函数）
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        # 创建深度思考LLM客户端
        # 深度思考LLM用于复杂的推理任务，如分析和决策
        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],  # 通常是更强大的模型，如gpt-5.2
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        
        # 创建快速思考LLM客户端
        # 快速思考LLM用于简单的任务，如数据处理和报告生成
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],  # 通常是更轻量的模型，如gpt-5-mini
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        # 获取配置好的LLM实例
        self.deep_thinking_llm = deep_client.get_llm()
        self.quick_thinking_llm = quick_client.get_llm()
        
        # Initialize memories
        # ========== 动态创建 researcher memories ==========
        self.selected_researchers = self.config.get("selected_researchers", DEFAULT_SELECTED_RESEARCHERS)
        self.researcher_memories: Dict[str, FinancialSituationMemory] = {}
        for key in self.selected_researchers:
            if key in RESEARCHER_REGISTRY:
                researcher_type = RESEARCHER_REGISTRY[key]["type"]
                self.researcher_memories[researcher_type] = FinancialSituationMemory(
                    researcher_type, self.config
                )
        
        self.trader_memory = FinancialSituationMemory("trader", self.config)
        self.invest_judge_memory = FinancialSituationMemory("research_manager", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager", self.config)
        
        # 从历史研究记录中学习
        if self.debug:
            logger.info("=" * 50)
            logger.info("📚 从历史研究记录中学习...")
            logger.info("=" * 50)
        
        for memory in self.researcher_memories.values():
            memory.learn_from_research_records()
        self.trader_memory.learn_from_research_records()
        self.invest_judge_memory.learn_from_research_records()
        self.risk_manager_memory.learn_from_research_records()

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config.get("max_debate_rounds", 2),
            max_risk_discuss_rounds=self.config.get("max_risk_discuss_rounds", 2),
            selected_researchers=self.selected_researchers,
        )
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.researcher_memories,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
            self.selected_researchers,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        """获取LLM客户端创建的提供商特定参数
        
        根据不同的LLM提供商，获取相应的特定参数
        
        Returns:
            提供商特定参数的字典
        """
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()

        # Google提供商特定参数
        if provider == "google":
            thinking_level = self.config.get("google_thinking_level")
            if thinking_level:
                kwargs["thinking_level"] = thinking_level

        # OpenAI提供商特定参数
        elif provider == "openai":
            reasoning_effort = self.config.get("openai_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort

        return kwargs

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """创建不同数据源的工具节点，使用抽象方法
        
        ToolNode是LangGraph提供的组件，用于执行工具函数并处理结果
        每个分析师类型都有自己的一组工具
        
        Returns:
            工具节点字典，键为分析师类型，值为对应的ToolNode
        """
        return {
            "market": ToolNode(
                [
                    # 核心股票数据工具
                    get_stock_data,
                    # 技术指标工具
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # 社交媒体分析的新闻工具
                    get_news,
                ]
            ),
            "news": ToolNode(
                [
                    # 新闻和内幕信息工具
                    get_news,
                    get_global_news,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # 基本面分析工具
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
            "candlestick": ToolNode(
                [
                    # 蜡烛图分析工具
                    get_stock_data,
                    get_indicators,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """运行交易代理图，处理指定公司在特定日期的交易
        
        这是核心执行方法，协调所有代理的工作流程
        
        Args:
            company_name: 公司股票代码 (如 "NVDA")
            trade_date: 交易日期 (如 "2026-01-15")
            
        Returns:
            元组 (final_state, processed_signal)
            - final_state: 图执行完成后的最终状态
            - processed_signal: 处理后的交易决策信号
        """

        self.ticker = company_name

        # 回测配置
        backtest_enabled = self.config.get("backtest", {}).get("enabled", True)
        if backtest_enabled:
            if self.debug:
                logger.info("=" * 50)
                logger.info("🔄 执行回测...")
                logger.info("=" * 50)
            run_backtest(symbol=company_name, target_date=trade_date, debug=self.debug)
            if self.debug:
                logger.info("")

        # 初始化状态
        # 创建代理的初始状态，包含公司信息和交易日期
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        try:
            if self.debug:
                # 调试模式，带跟踪输出
                # 使用stream方法逐块执行，便于调试和观察中间状态
                trace = []
                last_debate_state = None
                last_risk_state = None
                
                for chunk in self.graph.stream(init_agent_state, **args):
                    # 打印所有节点的消息
                    for node_name, node_data in chunk.items():
                        if node_name == "messages" and len(node_data) > 0:
                            logger.info("=" * 80)
                            logger.info("📝 Messages Output:")
                            logger.info("=" * 80)
                            node_data[-1].pretty_print()
                        elif node_name == "investment_debate_state":
                            logger.info("=" * 80)
                            logger.info("📊 Investment Debate State:")
                            logger.info("=" * 80)
                            logger.info("Count: %s", node_data.get('count', 0))
                            logger.info("Latest Speaker: %s", node_data.get('latest_speaker', 'N/A'))
                            # 动态输出所有 researcher 的历史
                            researcher_histories = node_data.get('researcher_histories', {})
                            for rtype, rhist in researcher_histories.items():
                                logger.info("--- %s History ---", rtype)
                                logger.info("%s", (rhist[:2000] if rhist else "N/A"))
                            logger.info("--- Current Response ---")
                            logger.info("%s", (node_data.get('current_response', '')[:2000] if node_data.get('current_response') else "N/A"))
                            logger.info("=" * 80)
                        elif node_name == "risk_debate_state":
                            logger.info("=" * 80)
                            logger.info("⚠️ Risk Debate State:")
                            logger.info("=" * 80)
                            logger.info("Count: %s", node_data.get('count', 0))
                            logger.info("Latest Speaker: %s", node_data.get('latest_speaker', 'N/A'))
                            logger.info("=" * 80)
                        elif node_name == "trader_investment_plan":
                            logger.info("=" * 80)
                            logger.info("💰 Trader Investment Plan:")
                            logger.info("=" * 80)
                            logger.info("%s", str(node_data)[:2000])
                            logger.info("=" * 80)
                    
                    trace.append(chunk)

                final_state = trace[-1] if trace else init_agent_state
            else:
                # 标准模式，不带跟踪
                # 使用invoke方法一次性执行完整个图
                final_state = self.graph.invoke(init_agent_state, **args)
        except Exception as e:
            logger.error("图执行失败 (%s @ %s): %s", company_name, trade_date, e)
            import traceback
            logger.debug("详细错误信息:\n%s", traceback.format_exc())
            raise

        # 存储当前状态用于反思
        self.curr_state = final_state

        # 记录状态到文件
        self._log_state(trade_date, final_state)

        # 返回决策和处理后的信号
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state（委托给persistence模块）"""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "candlestick_report": final_state["candlestick_report"],
            "investment_debate_state": {
                "researcher_histories": final_state["investment_debate_state"].get("researcher_histories", {}),
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"]["current_response"],
                "judge_decision": final_state["investment_debate_state"]["judge_decision"],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "aggressive_history": final_state["risk_debate_state"]["aggressive_history"],
                "conservative_history": final_state["risk_debate_state"]["conservative_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }
        
        # 委托给persistence模块
        self.persistence.save_all(final_state)
    
    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        # 动态反思所有 researcher
        for researcher_type, memory in self.researcher_memories.items():
            self.reflector.reflect_researcher(
                self.curr_state, returns_losses, memory, researcher_type
            )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
