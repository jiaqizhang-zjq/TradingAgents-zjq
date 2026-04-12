# TradingAgents 文档阅读指南

欢迎阅读 TradingAgents 项目文档！这里是文档的阅读顺序推荐，帮助您循序渐进地理解项目。

## 📖 推荐阅读顺序

### 第一步：了解项目整体结构

**[project_structure.md](project_structure.md)** - 完整目录结构与文件说明

阅读这个文档可以帮助您：
- 了解项目的整体目录结构
- 熟悉各个模块的功能和职责
- 掌握每个文件的定位

这是入门的最佳起点，让您对项目有一个宏观的认识。

---

### 第二步：理解系统架构

**[system_overview.md](system_overview.md)** - 系统总览与开发指南

阅读这个文档可以帮助您：
- 理解核心组件及其职责
- 了解数据流向和工作流程
- 掌握开发注意事项和常见问题

---

### 第三步：理解 LLM 调用流程

**[llm_call_chain.md](llm_call_chain.md)** - LLM 相关的函数调用关系链

阅读这个文档可以帮助您：
- 了解 LLM 客户端是如何创建的
- 掌握 LLM 在系统中的使用方式
- 理解工具调用的机制
- 熟悉数据流向

---

### 第四步：掌握 Agent 的使用

**[agents_guide.md](agents_guide.md)** - Agent 用法和解析指南

阅读这个文档可以帮助您：
- 理解 Agent 的创建模式
- 掌握 Prompt 的组织方式
- 学习工具调用的具体实现
- 了解 Graph 的组织方式

这是最详细的实操指南，包含代码示例和最佳实践。

---

### （可选）使用长桥 API

**[longbridge_guide.md](longbridge_guide.md)** - 长桥（Longbridge）API 使用指南

如果您只有长桥接口，需要替换 Alpha Vantage 和 Yahoo Finance，请阅读此文档。

---

## 📚 文档速查表

### 🏗️ 架构与概览

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [project_structure.md](project_structure.md) | 完整目录结构、文件说明 | ⭐ 入门 | 10 分钟 |
| [system_overview.md](system_overview.md) | 系统架构、开发指南、常见问题 | ⭐ 入门 | 15-20 分钟 |
| [langgraph_framework.md](langgraph_framework.md) | LangGraph 框架详解 | ⭐⭐⭐ 深入 | 30-40 分钟 |

### 🤖 代理与 LLM

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [agents_guide.md](agents_guide.md) | Agent 创建、Prompt 组织、工具调用 | ⭐⭐⭐ 深入 | 25-35 分钟 |
| [llm_call_chain.md](llm_call_chain.md) | LLM 调用流程、配置参数、数据流向 | ⭐⭐ 进阶 | 15-20 分钟 |
| [decision_weight_analysis.md](decision_weight_analysis.md) | 决策权重分析 | 📋 参考 | 5 分钟 |

### 💾 数据与存储

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [database.md](database.md) | 数据库表结构、字段说明 | ⭐⭐ 进阶 | 10-15 分钟 |
| [memory_system.md](memory_system.md) | 代理记忆系统 | ⭐⭐ 进阶 | 10-15 分钟 |

### 🔧 配置与工具

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [api_config_guide.md](api_config_guide.md) | 统一 API 配置管理 | ⭐ 入门 | 5-10 分钟 |
| [longbridge_guide.md](longbridge_guide.md) | 长桥 API 配置和使用 | ⭐⭐ 进阶 | 10-15 分钟 |
| [social_media_guide.md](social_media_guide.md) | 社交媒体数据（X/Twitter、Reddit） | ⭐⭐ 进阶 | 10-15 分钟 |
| [uv_guide.md](uv_guide.md) | uv 包管理器使用指南 | ⭐ 入门 | 5 分钟 |

### 📋 开发与历史

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [development_guide.md](development_guide.md) | 开发指南（项目百科全书） | ⭐⭐⭐ 深入 | 30+ 分钟 |
| [refactor_history.md](refactor_history.md) | 重构历史记录 | 📋 参考 | 按需 |

## 💡 阅读建议

1. **首次阅读**：按照推荐顺序完整阅读核心文档
2. **代码开发**：根据需要查阅特定文档
3. **问题排查**：先查看对应模块的文档，再查看代码注释
4. **二次阅读**：可以直接从感兴趣的部分开始

## 🔗 相关资源

- 项目根目录的 [README.md](../README.md) - 项目概览和快速开始
- `tradingagents/default_config.py` - 配置文件说明
- `tradingagents/graph/trading_graph.py` - 核心实现代码

## 📝 备注

- 所有文档都包含中文注释，方便理解
- 关键代码位置都有标注，可直接跳转查看
- 如有疑问，欢迎查阅代码或提交 Issue

祝您阅读愉快！🎉
