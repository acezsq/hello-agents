# ReAct Agent 学习总结

## 什么是 ReAct？

**ReAct = Reasoning (推理) + Acting (行动)**

一种让 AI 能够"思考"并"行动"的架构范式。

## 核心思想

**循环流程**: Thought → Action → Observation → Thought → ...

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Thought   │────→│   Action    │────→│ Observation │
│   (思考)     │     │   (行动)     │     │   (观察)     │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ↑─────────────────────────────────────────┘
```

## 工作流程示例

**问题**: "计算 25 * 4 + 100"

| 步骤 | Thought | Action | Observation |
|------|---------|--------|-------------|
| 1 | 先算乘法 25 * 4 | Calculator[25 * 4] | 100 |
| 2 | 再算 100 + 100 | Calculator[100 + 100] | 200 |
| 3 | 得到最终答案 | Finish[200] | 结束 |

## 代码结构

```
react_agent.py
├── MockLLM          # LLM 客户端（模拟/真实）
├── Tools            # 工具函数（计算器、天气等）
├── ToolExecutor     # 工具注册和管理
├── ReActAgent       # 核心循环逻辑
└── Prompt Template  # 提示词模板
```

## 核心类解析

### 1. ToolExecutor - 工具管理器

```python
class ToolExecutor:
    def register(self, name, description, func):
        # 注册工具：名称、描述、函数

    def get_tool(self, name) -> callable:
        # 根据名称获取工具函数

    def get_tool_descriptions(self) -> str:
        # 返回所有工具的文本描述（用于 Prompt）
```

### 2. ReActAgent - 主循环

```python
class ReActAgent:
    def run(self, question: str) -> str:
        for step in range(max_steps):
            # 1. 构建 Prompt（包含历史记录）
            prompt = build_prompt(question, history)

            # 2. LLM 生成 Thought + Action
            response = llm.think(prompt)
            thought, action = parse(response)

            # 3. 判断终止或继续
            if action.startswith("Finish"):
                return answer
            else:
                # 执行工具，获得观察结果
                observation = tool.execute(action)
                history.append(observation)  # 记录
```

### 3. Prompt 模板

```
你是一个智能助手，可以使用外部工具解决问题。

可用工具：
- Calculator: 计算器
- Weather: 天气查询

必须严格按以下格式回复：
Thought: 你的思考过程
Action: ToolName[input] 或 Finish[answer]

问题: {question}
历史记录: {history}
```

## 关键要点

| 要点 | 说明 |
|------|------|
| **循环执行** | 最多执行 max_steps 步，每轮都包含思考-行动-观察 |
| **格式约束** | LLM 必须输出 `Thought:` 和 `Action:` 格式 |
| **工具调用** | 通过 `ToolName[input]` 语法调用 |
| **终止条件** | 输出 `Finish[answer]` 时结束 |
| **历史记录** | 每轮的 Action 和 Observation 会保留，作为上下文 |

## 与 Plan-and-Solve 的区别

| ReAct | Plan-and-Solve |
|-------|----------------|
| 边思考边行动 | 先规划，后执行 |
| 适合工具调用 | 适合结构化推理 |
| 动态调整 | 固定步骤 |

## 实际应用场景

1. **搜索引擎集成** - ReAct + Google/Bing 搜索
2. **代码执行** - ReAct + Python 解释器
3. **API 调用** - ReAct + 各种 API 工具
4. **数据库查询** - ReAct + SQL 执行器

## 学习检查清单

- [x] 理解 ReAct 核心循环
- [x] 理解 ToolExecutor 的作用
- [x] 理解 Prompt 如何约束 LLM 输出
- [x] 能够运行基础示例
- [ ] 接入真实 LLM
- [ ] 添加自定义工具
- [ ] 处理复杂多步任务

---

*学习日期: 2026-03-24*
