# TradingAgents 项目结构说明

## 目录结构

```
TradingAgents/
├── run_trading.py             # 命令行入口（python run_trading.py [TICKER] [DATE] [选项]）
├── run_trading.sh             # Shell 启动脚本
├── reports.html               # 报告浏览页面
├── reports-server.sh          # 报告 HTTP 服务器启动脚本
│
├── cli/                       # 交互式 CLI 界面
│   ├── main.py               # CLI 主入口（python -m cli.main）
│   ├── config.py             # CLI 配置
│   ├── models.py             # CLI 数据模型
│   ├── utils.py              # CLI 工具函数
│   ├── stats_handler.py      # 统计信息处理
│   ├── announcements.py      # 公告通知
│   └── static/welcome.txt    # 欢迎文本
│
├── tradingagents/             # ====== 核心代码包 ======
│   ├── constants.py          # 常量定义（置信度、胜率、重试策略等）
│   ├── default_config.py     # DEFAULT_CONFIG 默认配置
│   ├── exceptions.py         # 自定义异常体系
│   ├── report_saver.py       # 报告保存（Markdown 格式）
│   │
│   ├── agents/               # 代理系统
│   │   ├── factory.py        # Agent 工厂 + Researcher 注册表
│   │   ├── backtest.py       # 回测系统（Backtrader 集成）
│   │   ├── backtest_stats.py # 回测统计
│   │   ├── backtest_utils.py # 回测工具函数
│   │   ├── prompt_templates.py # 提示词模板（中/英双语）
│   │   │
│   │   ├── analysts/         # 分析师团队
│   │   │   ├── market_analyst.py         # 市场分析师（技术指标）
│   │   │   ├── fundamentals_analyst.py   # 基本面分析师
│   │   │   ├── news_analyst.py           # 新闻分析师
│   │   │   ├── social_media_analyst.py   # 社交媒体分析师
│   │   │   └── candlestick_analyst.py    # K线分析师
│   │   │
│   │   ├── researchers/      # 研究员团队（动态注册表机制）
│   │   │   ├── base_researcher.py        # 抽象基类（统一逻辑）
│   │   │   ├── bull_researcher.py        # 看多研究员
│   │   │   ├── bear_researcher.py        # 看空研究员
│   │   │   ├── buffett_researcher.py     # 巴菲特价值投资风格
│   │   │   ├── cathie_wood_researcher.py # Cathie Wood 颠覆式创新风格
│   │   │   └── peter_lynch_researcher.py # Peter Lynch GARP 风格
│   │   │
│   │   ├── managers/         # 管理层
│   │   │   ├── research_manager.py       # 研究管理器（组织辩论）
│   │   │   └── risk_manager.py           # 风险管理器
│   │   │
│   │   ├── risk_mgmt/        # 风险辩论团队
│   │   │   ├── aggressive_debator.py     # 激进辩论者
│   │   │   ├── conservative_debator.py   # 保守辩论者
│   │   │   └── neutral_debator.py        # 中性辩论者
│   │   │
│   │   ├── trader/           # 交易员
│   │   │   └── trader.py                 # 综合决策 → BUY/SELL/HOLD
│   │   │
│   │   ├── prompts/          # 提示词模块
│   │   │   ├── base_templates.py         # 基础模板
│   │   │   └── perspectives.py           # 研究员视角定义
│   │   │
│   │   └── utils/            # 代理工具集
│   │       ├── agent_states.py           # 图状态 TypedDict
│   │       ├── agent_utils.py            # 抽象工具接口
│   │       ├── memory.py                 # 代理记忆管理
│   │       ├── memory_learner.py         # 记忆学习模块
│   │       ├── memory_storage.py         # 记忆持久化
│   │       ├── prediction_extractor.py   # 预测提取策略
│   │       ├── prompt_loader.py          # 提示词加载器
│   │       ├── logging_utils.py          # 日志工具
│   │       ├── core_stock_tools.py       # 核心股票数据工具
│   │       ├── fundamental_data_tools.py # 基本面数据工具
│   │       ├── technical_indicators_tools.py # 技术指标工具
│   │       ├── news_data_tools.py        # 新闻数据工具
│   │       ├── candlestick_tools.py      # K线数据工具
│   │       └── chart_patterns_tools.py   # 图表形态工具
│   │
│   ├── graph/                # LangGraph 编排引擎
│   │   ├── trading_graph.py  # 主编排类 TradingAgentsGraph
│   │   ├── setup.py          # 图构建（节点 + 边）
│   │   ├── propagation.py    # 执行逻辑
│   │   ├── conditional_logic.py # 路由逻辑（辩论轮次等）
│   │   ├── reflection.py     # 反思学习
│   │   ├── signal_processing.py # 信号处理
│   │   └── helpers/
│   │       └── persistence.py # 状态持久化
│   │
│   ├── dataflows/            # 数据流系统
│   │   ├── interface.py      # 数据接口层（路由分发）
│   │   ├── unified_data_manager.py # 统一数据管理器
│   │   ├── database.py       # Peewee ORM → SQLite
│   │   ├── research_tracker.py # 研究员胜率追踪
│   │   ├── data_cache.py     # API 响应缓存
│   │   ├── api_config.py     # API 密钥管理
│   │   ├── config.py         # 数据流配置
│   │   │
│   │   ├── core/             # 核心抽象
│   │   │   ├── vendor_registry.py    # 数据供应商注册
│   │   │   ├── retry_policy.py       # 重试策略
│   │   │   ├── statistics_collector.py # 统计收集
│   │   │   ├── data_parser.py        # 数据解析
│   │   │   ├── date_adjuster.py      # 日期调整
│   │   │   ├── error_detector.py     # 错误检测
│   │   │   └── indicator_helper.py   # 指标辅助
│   │   │
│   │   ├── indicators/       # 技术指标模块
│   │   │   ├── moving_averages.py    # 移动平均线
│   │   │   ├── momentum_indicators.py # 动量指标
│   │   │   ├── trend_indicators.py   # 趋势指标
│   │   │   ├── volume_indicators.py  # 成交量指标
│   │   │   └── additional_indicators.py # 附加指标
│   │   │
│   │   ├── patterns/         # 形态识别
│   │   │   ├── candlestick_patterns.py # K线形态
│   │   │   ├── chart_patterns.py     # 图表形态
│   │   │   └── detectors/utils.py    # 检测工具
│   │   │
│   │   ├── tracker/          # 研究员追踪
│   │   │   ├── models.py    # 数据模型
│   │   │   └── tracker.py   # 追踪逻辑
│   │   │
│   │   ├── vendors/          # 数据供应商
│   │   │   └── longbridge_client.py  # 长桥客户端
│   │   │
│   │   ├── # 数据源实现
│   │   ├── longbridge.py             # 长桥 API
│   │   ├── y_finance.py              # Yahoo Finance
│   │   ├── y_finance_financials.py   # YF 财务数据
│   │   ├── y_finance_indicators.py   # YF 技术指标
│   │   ├── yfinance_news.py          # YF 新闻
│   │   ├── alpha_vantage.py          # Alpha Vantage 入口
│   │   ├── alpha_vantage_common.py   # AV 通用
│   │   ├── alpha_vantage_stock.py    # AV 股票
│   │   ├── alpha_vantage_indicator.py # AV 指标
│   │   ├── alpha_vantage_fundamentals.py # AV 基本面
│   │   ├── alpha_vantage_news.py     # AV 新闻
│   │   ├── social_media.py           # Reddit/Twitter
│   │   │
│   │   ├── # 指标计算
│   │   ├── complete_indicators.py    # 完整指标列表
│   │   ├── lazy_indicators.py        # 惰性计算器
│   │   ├── incremental_indicators.py # 增量计算
│   │   ├── indicator_groups.py       # 指标分组
│   │   ├── stockstats_utils.py       # stockstats 工具
│   │   │
│   │   └── # 其他
│   │       ├── async_data_loader.py  # 异步数据加载
│   │       ├── data_preloader.py     # 数据预加载
│   │       ├── db_exporters.py       # 数据库导出
│   │       ├── vendor_models.py      # 供应商数据模型
│   │       └── utils.py              # 数据流工具函数
│   │
│   ├── llm_clients/          # LLM 客户端系统
│   │   ├── factory.py        # 客户端工厂
│   │   ├── base_client.py    # 抽象基类
│   │   ├── openai_client.py  # OpenAI/xAI/Ollama/OpenRouter
│   │   ├── anthropic_client.py # Anthropic Claude
│   │   ├── google_client.py  # Google Gemini
│   │   ├── validators.py     # 模型验证器
│   │   └── KNOWN_ISSUES.md   # 已知问题清单
│   │
│   ├── core/                 # 核心基础设施
│   │   └── container.py      # 依赖注入容器
│   │
│   ├── utils/                # 全局工具模块
│   │   ├── validators.py     # 输入验证器
│   │   ├── logger.py         # 统一日志
│   │   └── performance_monitor.py # 性能监控
│   │
│   └── prompts/              # 提示词目录（预留）
│
├── tests/                     # 测试目录
│   ├── conftest.py           # pytest 配置/fixtures
│   ├── unit/                 # 单元测试（17 个）
│   ├── benchmarks/           # 性能基准测试
│   ├── fixtures/             # 测试 fixtures（预留）
│   └── integration/          # 集成测试（预留）
│
├── doc/                       # 项目文档
│   ├── README.md             # 文档阅读指南
│   ├── project_structure.md  # 项目结构（本文件）
│   ├── system_overview.md    # 系统总览
│   ├── agents_guide.md       # 代理系统指南
│   ├── api_config_guide.md   # API 配置指南
│   ├── database.md           # 数据库设计
│   ├── decision_weight_analysis.md # 决策权重分析
│   ├── development_guide.md  # 开发指南（项目百科）
│   ├── langgraph_framework.md # LangGraph 框架详解
│   ├── llm_call_chain.md     # LLM 调用链
│   ├── longbridge_guide.md   # 长桥 API 指南
│   ├── memory_system.md      # 记忆系统
│   ├── refactor_history.md   # 重构历史记录
│   ├── social_media_guide.md # 社交媒体指南
│   └── uv_guide.md           # uv 包管理器指南
│
├── assets/                    # 项目图片资源
├── reports/                   # 运行时生成的分析报告（gitignored）
├── eval_results/              # 评估结果（gitignored）
│
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略规则
├── LICENSE                    # Apache 2.0 许可证
├── README.md                  # 项目主说明
├── pyproject.toml             # Python 项目配置
├── requirements.txt           # pip 依赖项
├── mypy.ini                   # mypy 类型检查配置
├── pytest.ini                 # pytest 配置
└── uv.lock                   # uv 锁文件
```

## 核心模块详解

### 1. 代理系统 (`tradingagents/agents/`)

框架采用**层次化多代理架构**，代理按角色专业化。

#### 分析师团队 (`analysts/`)

| 文件 | 职责 | 关键工具 |
|------|------|----------|
| `market_analyst.py` | 市场趋势、技术指标分析 | get_stock_data, get_indicators |
| `fundamentals_analyst.py` | 财务报表、资产负债表分析 | get_fundamentals, get_balance_sheet |
| `news_analyst.py` | 新闻事件、宏观经济分析 | get_news, get_global_news |
| `social_media_analyst.py` | Reddit/Twitter 情绪分析 | get_social_media_data |
| `candlestick_analyst.py` | K线形态、价格行为分析 | get_candlestick_patterns |

#### 研究员团队 (`researchers/`)

使用 **RESEARCHER_REGISTRY** 动态注册表机制，支持 N-way 多方辩论。

| 文件 | 角色 | 风格 |
|------|------|------|
| `base_researcher.py` | 抽象基类 | 统一 Bull/Bear 逻辑 |
| `bull_researcher.py` | 看多研究员 | 识别机会和增长潜力 |
| `bear_researcher.py` | 看空研究员 | 识别风险和危险信号 |
| `buffett_researcher.py` | 巴菲特研究员 | 价值投资、安全边际 |
| `cathie_wood_researcher.py` | Cathie Wood 研究员 | 颠覆式创新 |
| `peter_lynch_researcher.py` | Peter Lynch 研究员 | GARP 成长合理价 |

#### 其他代理

| 模块 | 角色 |
|------|------|
| `managers/research_manager.py` | 组织多轮辩论，追踪历史胜率 |
| `managers/risk_manager.py` | 评估投资组合风险 |
| `risk_mgmt/*.py` | 激进/保守/中性三方风险辩论 |
| `trader/trader.py` | 综合决策 → BUY/SELL/HOLD + 仓位 |

### 2. LangGraph 编排引擎 (`tradingagents/graph/`)

使用 **LangGraph** 构建有状态的有向图。

| 文件 | 职责 |
|------|------|
| `trading_graph.py` | 主编排类，初始化 LLM、构建图 |
| `setup.py` | 节点创建和边定义（支持动态研究员注册） |
| `propagation.py` | 创建初始状态，流式执行图 |
| `conditional_logic.py` | 路由逻辑（工具调用/辩论轮次） |
| `reflection.py` | 决策后反思学习 |
| `signal_processing.py` | 信号聚合处理 |

### 3. 数据流系统 (`tradingagents/dataflows/`)

| 模块 | 职责 |
|------|------|
| `interface.py` | 数据接口层，路由到配置的供应商 |
| `unified_data_manager.py` | 统一数据管理，多源优先级 |
| `database.py` | Peewee ORM → SQLite 持久化 |
| `research_tracker.py` | 研究员胜率追踪 |
| `core/` | 核心抽象（注册表、重试策略、统计等） |
| `indicators/` | 技术指标模块（5 类） |
| `patterns/` | K线形态和图表形态识别 |

**数据供应商**：Alpha Vantage · Yahoo Finance · 长桥 Longbridge · Reddit/Twitter

### 4. LLM 客户端 (`tradingagents/llm_clients/`)

统一不同 LLM 提供商接口，支持 **双 LLM 策略**（Deep Think + Quick Think）。

支持提供商：OpenAI · Anthropic · Google · xAI · OpenRouter · Ollama

### 5. 配置系统

- `constants.py` — 置信度、胜率、重试、缓存等常量
- `default_config.py` — `DEFAULT_CONFIG` 默认配置字典
- `dataflows/config.py` — 数据流配置管理（`get_config` / `set_config`）
- `dataflows/api_config.py` — API 密钥管理
- `.env` — API 密钥（通过环境变量管理）

## 开发规范

### 命名规范

- 文件：小写下划线（`market_analyst.py`）
- 类：大驼峰（`TradingAgentsGraph`）
- 函数：小写下划线（`get_stock_data`）
- 常量：大写下划线（`DEFAULT_CONFIG`）

### 扩展指南

**添加新研究员**：在 `agents/researchers/` 创建继承 `BaseResearcher` 的类，在 `constants.py` 的 `RESEARCHER_REGISTRY` 中注册。

**添加新分析师**：在 `agents/analysts/` 创建文件，在 `setup.py` 中注册节点和边。

**添加新数据供应商**：在 `dataflows/` 创建实现，在 `unified_data_manager.py` 添加路由。

**添加新 LLM 提供商**：在 `llm_clients/` 创建继承 `BaseLLMClient` 的客户端，在 `factory.py` 添加路由。

## 版本历史

### v0.3.0 (2026-04)
- Researcher Registry 动态化重构
- 新增 3 种投资风格研究员（Buffett / Cathie Wood / Peter Lynch）
- N-way round-robin 辩论路由
- Memory Learner / Memory Storage 模块
- 自定义异常体系

### v0.2.0 (2026-02 ~ 2026-03)
- 安全修复（SQL 注入、输入验证）
- 惰性指标计算（性能提升 60-80%）
- BaseResearcher 抽象基类
- 依赖注入容器
- 单元测试框架（17+ 测试）
- 长桥 API 支持
- 中文语言支持

### v0.1.0 (2025-12)
- 初始版本发布
- 基础多代理框架
- Alpha Vantage 和 Yahoo Finance 支持
