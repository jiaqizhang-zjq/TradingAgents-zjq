"""
基础研究员类 - 消除 Bull/Bear Researcher 的重复代码
"""

from langchain_core.messages import AIMessage
import time
import json
import re
from typing import Callable, Dict, Any

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config


class BaseResearcher:
    """
    基础研究员类
    
    提供所有研究员（Bull/Bear/Buffett/CathieWood/PeterLynch...）的通用逻辑。
    新增研究员只需提供 system_prompts、stance 和 speaker_label。
    """
    
    # 研究排分组定义：每个排侧重的报告字段
    RESEARCH_GROUP_FIELDS = {
        "technical": ["market_report", "candlestick_report"],
        "fundamentals": ["fundamentals_report"],
        "sentiment": ["sentiment_report", "news_report"],
        None: ["market_report", "sentiment_report", "news_report", "fundamentals_report", "candlestick_report"],  # 全量（向后兼容）
    }

    def __init__(
        self,
        researcher_type: str,
        system_prompts: Dict[str, str],
        llm,
        memory,
        default_win_rate: float = 0.50,
        stance_zh: str = "",
        stance_en: str = "",
        speaker_label: str = "",
        research_group: str = None,
    ):
        """
        初始化基础研究员
        
        Args:
            researcher_type: 研究员类型标识 (如 "bull_researcher", "buffett_researcher")
            system_prompts: 系统提示词字典 {"en": ..., "zh": ...}
            llm: LLM 客户端
            memory: 记忆存储
            default_win_rate: 默认胜率
            stance_zh: 中文立场标签（如 "看涨", "巴菲特价值投资"）
            stance_en: 英文立场标签（如 "bullish", "Buffett value investing"）
            speaker_label: 辩论中的发言者标签（如 "Bull", "Buffett"），用于轮流发言
            research_group: 研究排分组（"technical"/"fundamentals"/"sentiment"/None）
                           决定该研究员侧重哪些数据源
        """
        self.researcher_type = researcher_type
        self.system_prompts = system_prompts
        self.llm = llm
        self.memory = memory
        self.default_win_rate = default_win_rate
        self.stance_zh = stance_zh or self._default_stance_zh()
        self.stance_en = stance_en or self._default_stance_en()
        self.speaker_label = speaker_label or self._default_speaker_label()
        self.research_group = research_group
    
    def _build_win_rate_string(
        self,
        symbol: str,
        language: str,
        tracker: Any
    ) -> str:
        """构建胜率信息字符串"""
        # 获取特定股票的胜率
        symbol_win_rate = tracker.get_researcher_win_rate(
            self.researcher_type, symbol, default_win_rate=self.default_win_rate
        )
        # 获取研究员平均胜率
        avg_win_rate = tracker.get_researcher_win_rate(
            self.researcher_type, None, default_win_rate=self.default_win_rate
        )
        
        # 构建胜率信息字符串
        if language == "zh":
            if symbol_win_rate['total_predictions'] >= 1:
                symbol_part = f"该股票胜率：{symbol_win_rate['win_rate']:.1%}（{symbol_win_rate['total_predictions']}次）"
            else:
                symbol_part = "该股票暂无历史数据"
            
            avg_part = f"平均胜率：{avg_win_rate['win_rate']:.1%}（{avg_win_rate['total_predictions']}次）"
            return f"{symbol_part} | {avg_part}"
        else:
            if symbol_win_rate['total_predictions'] >= 1:
                symbol_part = f"This stock: {symbol_win_rate['win_rate']:.1%} ({symbol_win_rate['total_predictions']} trades)"
            else:
                symbol_part = "No history for this stock"
            
            avg_part = f"Average: {avg_win_rate['win_rate']:.1%} ({avg_win_rate['total_predictions']} trades)"
            return f"{symbol_part} | {avg_part}"
    
    def _filter_reports_by_group(
        self,
        market_research_report: str,
        sentiment_report: str,
        news_report: str,
        fundamentals_report: str,
        candlestick_report: str,
        language: str,
    ) -> Dict[str, str]:
        """根据 research_group 过滤报告，只保留本排相关的数据"""
        all_reports = {
            "market_report": market_research_report,
            "sentiment_report": sentiment_report,
            "news_report": news_report,
            "fundamentals_report": fundamentals_report,
            "candlestick_report": candlestick_report,
        }
        
        focused_fields = self.RESEARCH_GROUP_FIELDS.get(
            self.research_group,
            self.RESEARCH_GROUP_FIELDS[None]
        )
        
        omitted = "（非本排重点，已省略）" if language == "zh" else "(Not in scope for this research group, omitted)"
        
        filtered = {}
        for key, value in all_reports.items():
            if key in focused_fields:
                filtered[key] = value
            else:
                filtered[key] = omitted
        
        return filtered

    def _build_prompt(
        self,
        language: str,
        win_rate_str: str,
        market_research_report: str,
        sentiment_report: str,
        news_report: str,
        fundamentals_report: str,
        candlestick_report: str,
        history: str,
        current_response: str,
        past_memory_str: str,
    ) -> str:
        """构建提示词（模板方法）- 通用版本，不假设特定对手"""
        system_prompt = self.system_prompts.get(language, self.system_prompts["zh"])
        stance_label = self._get_stance_zh() if language == "zh" else self._get_stance_en()
        
        # 根据研究排分组过滤报告
        reports = self._filter_reports_by_group(
            market_research_report, sentiment_report, news_report,
            fundamentals_report, candlestick_report, language,
        )
        
        # 构建研究排标识
        group_label = ""
        if self.research_group:
            group_names = {
                "technical": ("技术排", "Technical Research Group"),
                "fundamentals": ("基本面排", "Fundamentals Research Group"),
                "sentiment": ("消息排", "Sentiment/News Research Group"),
            }
            zh_name, en_name = group_names.get(self.research_group, ("", ""))
            if language == "zh":
                group_label = f"\n\n【所属研究排：{zh_name}】\n你是{zh_name}的研究员，请重点基于本排核心数据进行分析和辩论。\n"
            else:
                group_label = f"\n\n[Research Group: {en_name}]\nYou are a researcher in the {en_name}. Focus your analysis and debate on the core data of your group.\n"
        
        if language == "zh":
            return f"""{system_prompt}{group_label}

【历史胜率参考】
{win_rate_str}
请结合你的历史表现来调整本次分析的置信度。如果你的历史胜率高于行业均值，可以适度提高置信度；如果低于均值，需要更加谨慎。

可用资源：
市场研究报告：{reports['market_report']}
社交媒体情绪报告：{reports['sentiment_report']}
最新世界事务新闻：{reports['news_report']}
公司基本面报告：{reports['fundamentals_report']}
蜡烛图分析报告：{reports['candlestick_report']}
辩论对话历史：{history}
上一位辩论者的论点：{current_response}
类似情况下的反思和经验教训：{past_memory_str}
利用这些信息从你的{stance_label}视角提出一个令人信服的论点，回应其他辩论者的观点，并参与一场动态辩论，展示你的立场优势。你还必须解决反思问题，并从过去的经验教训中学习。"""
        else:
            return f"""{system_prompt}{group_label}

[HISTORICAL WIN RATE REFERENCE]
{win_rate_str}
Please adjust your confidence level based on your historical performance. If your win rate is above industry average, you can moderately increase confidence; if below, be more cautious.

Resources available:
Market research report: {reports['market_report']}
Social media sentiment report: {reports['sentiment_report']}
Latest world affairs news: {reports['news_report']}
Company fundamentals report: {reports['fundamentals_report']}
Candlestick analysis report: {reports['candlestick_report']}
Debate conversation history: {history}
Last debater's argument: {current_response}
Reflections and lessons learned from similar situations: {past_memory_str}
Use this information to make a compelling {stance_label} case from your perspective, respond to other debaters' arguments, and engage in a dynamic debate showcasing the strengths of your position. You must also address the reflection questions and learn from past lessons."""
    
    def _default_stance_zh(self) -> str:
        """默认中文立场（向后兼容 bull/bear）"""
        if "bull" in self.researcher_type:
            return "看涨"
        elif "bear" in self.researcher_type:
            return "看跌"
        return self.researcher_type.replace("_researcher", "")
    
    def _default_stance_en(self) -> str:
        """默认英文立场（向后兼容 bull/bear）"""
        if "bull" in self.researcher_type:
            return "bullish"
        elif "bear" in self.researcher_type:
            return "bearish"
        return self.researcher_type.replace("_researcher", "")
    
    def _default_speaker_label(self) -> str:
        """默认发言标签"""
        if "bull" in self.researcher_type:
            return "Bull"
        elif "bear" in self.researcher_type:
            return "Bear"
        return self.researcher_type.replace("_researcher", "").title()

    def _get_stance_zh(self) -> str:
        """获取立场的中文描述"""
        return self.stance_zh
    
    def _get_stance_en(self) -> str:
        """获取立场的英文描述"""
        return self.stance_en
    
    def _parse_llm_response(
        self,
        response_content: str,
        symbol: str,
        trade_date: str,
        language: str
    ) -> Dict[str, Any]:
        """
        解析 LLM 响应
        
        返回格式：
        {
            "recommendation": str,
            "confidence": float,
            "reasoning": str
        }
        """
        recommendation = "HOLD"
        confidence = 0.0
        reasoning = response_content

        # 提取推荐
        if language == "zh":
            if "推荐：买入" in response_content or "推荐：BUY" in response_content:
                recommendation = "BUY"
            elif "推荐：卖出" in response_content or "推荐：SELL" in response_content:
                recommendation = "SELL"
            elif "推荐：持有" in response_content or "推荐：HOLD" in response_content:
                recommendation = "HOLD"
        else:
            if "Recommendation: BUY" in response_content:
                recommendation = "BUY"
            elif "Recommendation: SELL" in response_content:
                recommendation = "SELL"
            elif "Recommendation: HOLD" in response_content:
                recommendation = "HOLD"

        # 提取置信度
        confidence_pattern = r"(?:置信度|Confidence)[：:]\s*([0-9]+(?:\.[0-9]+)?)"
        match = re.search(confidence_pattern, response_content)
        if match:
            try:
                confidence = float(match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0
            except ValueError:
                confidence = 0.0

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def create_node(self) -> Callable:
        """
        创建研究员节点函数
        
        Returns:
            节点函数
        """
        def node_function(state) -> dict:
            investment_debate_state = state["investment_debate_state"]
            history = investment_debate_state.get("history", "")
            
            # 从 researcher_histories Dict 获取本研究员的历史
            researcher_histories = investment_debate_state.get("researcher_histories", {})
            researcher_history = researcher_histories.get(self.researcher_type, "")

            current_response = investment_debate_state.get("current_response", "")
            market_research_report = state["market_report"]
            sentiment_report = state["sentiment_report"]
            news_report = state["news_report"]
            fundamentals_report = state["fundamentals_report"]
            candlestick_report = state.get("candlestick_report", "")
            
            # 获取股票和日期信息
            symbol = state.get("company_of_interest", "UNKNOWN")
            trade_date = state.get("trade_date", "")
            
            # 获取语言配置
            config = get_config()
            language = config.get("output_language", "zh")

            curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
            past_memories = self.memory.get_memories(curr_situation, n_matches=2)

            past_memory_str = ""
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"

            # 获取历史胜率
            tracker = get_research_tracker()
            win_rate_str = self._build_win_rate_string(symbol, language, tracker)
            
            # 构建提示词（不再需要 opponent_stance）
            prompt = self._build_prompt(
                language=language,
                win_rate_str=win_rate_str,
                market_research_report=market_research_report,
                sentiment_report=sentiment_report,
                news_report=news_report,
                fundamentals_report=fundamentals_report,
                candlestick_report=candlestick_report,
                history=history,
                current_response=current_response,
                past_memory_str=past_memory_str,
            )
            
            # 调用 LLM
            messages = [{"role": "user", "content": prompt}]
            result = self.llm.invoke(messages)
            response_content = result.content if hasattr(result, "content") else str(result)

            # 解析响应
            parsed = self._parse_llm_response(response_content, symbol, trade_date, language)
            recommendation = parsed["recommendation"]
            confidence = parsed["confidence"]
            reasoning = parsed["reasoning"]

            # 保存研究记录
            tracker.save_research_record(
                researcher_name=self.researcher_type,
                researcher_type=self.researcher_type,
                symbol=symbol,
                trade_date=trade_date,
                prediction=recommendation,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "language": language,
                    "win_rate_str": win_rate_str
                }
            )

            # 更新状态
            stance_label = self._get_stance_zh() if language == 'zh' else self._get_stance_en()
            updated_history = f"{history}\n\n{stance_label}: {response_content}"
            updated_researcher_history = f"{researcher_history}\n\n{response_content}"

            investment_debate_state["history"] = updated_history
            investment_debate_state["current_response"] = response_content
            
            # 使用 speaker_label 用于 conditional_logic 判断
            investment_debate_state["latest_speaker"] = self.speaker_label
            
            # 更新 count 用于轮次控制
            current_count = investment_debate_state.get("count", 0)
            investment_debate_state["count"] = current_count + 1
            
            # 更新 researcher_histories Dict（而不是硬编码的 bull_history/bear_history）
            researcher_histories[self.researcher_type] = updated_researcher_history
            investment_debate_state["researcher_histories"] = researcher_histories

            time.sleep(1)

            return {"investment_debate_state": investment_debate_state}
        
        return node_function
