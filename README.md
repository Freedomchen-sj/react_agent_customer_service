# 智扫通机器人售后系统（ReAct Agent）
基于 LangChain 1.x `create_agent` 构建的扫地/扫拖机器人智能体，覆盖三类场景：**知识问答（RAG）**、**环境适配建议（天气工具）**、**个性化使用报告（外部数据 + 动态提示词切换）**。

## 核心特性

- **ReAct 自主编排**：模型自主完成「思考 → 工具调用 → 观察 → 再思考」循环，编排 7 个工具解决多场景问题
- **中间件钩子**：`wrap_tool_call` 全链路监控工具调用（参数/结果/异常）；`before_model` 观测模型输入状态；`dynamic_prompt` 依据运行时上下文在「客服」与「报告写手」双系统提示词间动态切换，实现场景感知的提示词路由
- **ToolRuntime 上下文注入**：用户 ID、月份、城市由前端侧边栏注入工具运行时，而非让 LLM 猜测"当前用户是谁"，保证报告数据稳定命中
- **RAG 知识库**：5 篇领域文档（100+ 条目，条目级标签 + FAQ 兜底 + 同义词埋点格式），RecursiveCharacterTextSplitter 语义分块 + Chroma 向量检索 + MD5 文件级增量入库
- **真实天气 + 降级兜底**：接入 wttr.in 实时天气 API，请求失败自动降级为默认描述，不阻断对话链路
- **流式输出**：Streamlit 多轮会话 + 逐字符打字机式流式响应

## 架构

```
app.py (Streamlit UI)
  └─ ReactAgent (agent/react_agent.py)
       ├─ create_agent: chat_model + 7 tools + 3 middleware
       ├─ 工具层 (agent/tools/agent_tools.py)
       │    ├─ rag_summarize ──→ RagSummarizeService (LCEL链)
       │    │                      └─ VectorStoreService (Chroma + MD5增量入库)
       │    ├─ get_weather ──→ wttr.in API（失败降级）
       │    ├─ get_user_id / get_current_month / get_user_location
       │    │      └─ ToolRuntime 读取前端注入的运行时上下文
       │    ├─ fetch_external_data ──→ data/external/records.csv
       │    └─ fill_context_for_report ──→ 触发提示词切换信号
       └─ 中间件层 (agent/tools/middleware.py)
            ├─ monitor_tool: 工具监控 + 置 report 标记
            ├─ log_before_model: 模型调用前状态日志
            └─ report_prompt_switch: 双提示词动态路由
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置模型 API Key（阿里云百炼 DashScope）
set DASHSCOPE_API_KEY=你的key        # Windows
# export DASHSCOPE_API_KEY=你的key   # Linux/Mac

# 3. 启动（在项目父目录执行，包名需与目录名一致）
python -m streamlit run react_agent_customer_service/app.py
```

首次启动会自动将 `data/` 下的知识库文档切分、向量化并写入 Chroma（`chroma_db/`、`logs/` 为运行时产物，已在 .gitignore 中排除）。

## 目录结构

```
react_agent_customer_service/
├── app.py                 # Streamlit 入口（含侧边栏运行时上下文）
├── agent/                 # ReAct Agent 与工具、中间件
├── rag/                   # RAG 服务与向量库服务
├── model/                 # 模型工厂（对话/嵌入模型抽象）
├── prompts/               # 系统提示词（客服/RAG总结/报告写手）
├── config/                # YAML 配置（模型/向量库/提示词路径）
├── data/                  # 知识库文档 + 用户使用记录 CSV
└── utils/                 # 配置加载/文件处理/日志/路径工具
```

## 工程难点与解法

| 难点 | 解法 | 效果 |
|---|---|---|
| 身份参数幻觉：LLM 无法得知"当前用户"，报告数据随机错配 | ToolRuntime 从前端注入 user_id/month/city，不进模型参数、不暴露进 function schema | 报告链路命中率 25% → 100% |
| 工具调用失败可能中断对话链路 | wrap_tool_call 中间件统一捕获异常并记录参数/结果日志；天气 API 设 8s 超时 + 降级兜底文案 | 故障注入演练通过，单点失败不阻断对话 |
| RAG 幻觉 | 提示词强约束"仅基于参考资料作答、信息不足显式拒答"；系统提示词设 5 次工具调用止损上限防 ReAct 死循环 | 答案可溯源（条目级标签） |
| 客服/报告双场景提示词冲突 | fill_context_for_report 信号弹 + monitor_tool 置标记 + dynamic_prompt 运行时路由 | 单 Agent 双人格无冲突切换 |

## 性能实测（2026-09，qwen3-max，自建基准脚本）

- 5 篇 100+ 条目知识库全量构建（切分+向量化+入库）：**11s**
- RAG 工具端到端：**P50 1.9s / P95 2.4s**（prompt 约束输出长度，延迟较无约束版本降约 3 倍）
- ReAct 单工具问答端到端 ≈ 17.6s；多工具报告链（4 步编排）≈ 27.7s
- 瓶颈定位：多轮模型调用串行；优化方向：工具并行调用、小模型路由、高频问答缓存

## 技术栈

Python · LangChain 1.x create_agent（middleware / ToolRuntime）· Chroma · 阿里云百炼 qwen3-max · DashScope Embedding · Streamlit · wttr.in
