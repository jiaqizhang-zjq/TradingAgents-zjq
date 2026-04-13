# TradingAgents/graph/setup.py

import importlib
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import (
    create_market_analyst,
    create_social_media_analyst,
    create_news_analyst,
    create_fundamentals_analyst,
    create_candlestick_analyst,
    create_msg_delete,
    create_research_manager,
    create_trader,
    create_aggressive_debator,
    create_neutral_debator,
    create_conservative_debator,
    create_risk_manager,
)
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.constants import RESEARCHER_REGISTRY, DEFAULT_SELECTED_RESEARCHERS

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        researcher_memories: Dict[str, Any],  # key: researcher_type, value: memory
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
        selected_researchers: List[str] = None,
    ):
        """Initialize with required components.
        
        Args:
            quick_thinking_llm: 快速思考 LLM
            deep_thinking_llm: 深度思考 LLM
            tool_nodes: 工具节点字典
            researcher_memories: researcher memory 字典，key 为 researcher_type
            trader_memory: 交易员 memory
            invest_judge_memory: 投资裁判 memory
            risk_manager_memory: 风险管理 memory
            conditional_logic: 条件逻辑控制器
            selected_researchers: 选中的 researcher 列表
        """
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.researcher_memories = researcher_memories
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic
        self.selected_researchers = selected_researchers or DEFAULT_SELECTED_RESEARCHERS

    def _create_researcher_node(self, researcher_key: str):
        """通过注册表动态创建 researcher 节点.
        
        Args:
            researcher_key: researcher 简称（如 "bull", "bear", "buffett"）
            
        Returns:
            节点函数
        """
        info = RESEARCHER_REGISTRY[researcher_key]
        module = importlib.import_module(info["module"])
        factory_fn = getattr(module, info["factory"])
        memory = self.researcher_memories.get(info["type"])
        return factory_fn(self.quick_thinking_llm, memory)

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals", "candlestick"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
                - "candlestick": Candlestick analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes (data-driven)
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        analyst_factory_map = {
            "market": create_market_analyst,
            "social": create_social_media_analyst,
            "news": create_news_analyst,
            "fundamentals": create_fundamentals_analyst,
            "candlestick": create_candlestick_analyst,
        }

        for analyst_type in selected_analysts:
            factory = analyst_factory_map.get(analyst_type)
            if factory is None:
                raise ValueError(f"Unknown analyst type: {analyst_type}")
            analyst_nodes[analyst_type] = factory(self.quick_thinking_llm)
            delete_nodes[analyst_type] = create_msg_delete()
            tool_nodes[analyst_type] = self.tool_nodes[analyst_type]

        # ========== 动态创建 researcher 节点 ==========
        researcher_nodes = {}  # display_name -> node_function
        for key in self.selected_researchers:
            if key not in RESEARCHER_REGISTRY:
                raise ValueError(f"Unknown researcher: {key}. Available: {list(RESEARCHER_REGISTRY.keys())}")
            info = RESEARCHER_REGISTRY[key]
            display_name = info["display_name"]
            researcher_nodes[display_name] = self._create_researcher_node(key)

        # Create manager and trader nodes
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        risk_manager_node = create_risk_manager(
            self.deep_thinking_llm, self.risk_manager_memory
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # ========== 添加动态 researcher 节点 ==========
        for display_name, node in researcher_nodes.items():
            workflow.add_node(display_name, node)

        # Add other nodes
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Risk Judge", risk_manager_node)

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        first_researcher_display = self.conditional_logic.debate_order[0]
        
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to first researcher
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, first_researcher_display)

        # ========== 为每个 researcher 添加条件边 ==========
        # 每个 researcher 都走同一个 should_continue_debate，路由到下一个 researcher 或 Research Manager
        all_researcher_destinations = {name: name for name in researcher_nodes.keys()}
        all_researcher_destinations["Research Manager"] = "Research Manager"
        
        for display_name in researcher_nodes.keys():
            workflow.add_conditional_edges(
                display_name,
                self.conditional_logic.should_continue_debate,
                all_researcher_destinations,
            )

        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", END)

        # Compile and return
        return workflow.compile()
