# Plan-and-Solve 学习总结

## 什么是 Plan-and-Solve？

**Plan-and-Solve = 先规划(Plan) + 后执行(Solve)**

一种将复杂问题分解为有序步骤，然后逐步解决的架构范式。

## 核心思想

**两阶段工作流**:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    用户问题  │─────→│   Planner   │─────→│   步骤列表   │
│  (Question) │      │  (规划器)    │      │   (Plan)    │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                                                  ↓
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   最终答案   │←─────│   Executor  │←─────│   逐步执行   │
│  (Answer)   │      │  (执行器)    │      │ (Step-by-Step)
└─────────────┘      └─────────────┘      └─────────────┘
```

## 与 ReAct 的区别

| 特性 | Plan-and-Solve | ReAct |
|------|----------------|-------|
| **工作方式** | 先规划，后执行 | 边思考边行动 |
| **步骤数量** | 提前确定 | 动态决定 |
| **适用场景** | 结构化任务 | 探索性任务 |
| **可预测性** | 高 | 中 |
| **错误恢复** | 规划后难以调整 | 灵活调整 |

## 代码结构

```
plan_and_solve_agent.py
├── HelloAgentsLLM    # LLM 客户端（复用 ReAct 版本）
├── Planner           # 规划器 - 分解问题为步骤
├── Executor          # 执行器 - 按步骤执行
└── PlanAndSolveAgent # 主 Agent - 协调规划与执行
```

## 核心类解析

### 1. Planner (规划器)

```python
class Planner:
    def plan(self, question: str) -> List[str]:
        """
        将问题分解为步骤列表

        输入: "帮我制定一个学习 Python 的 3 周计划"
        输出: [
            "安装 Python 和 VS Code",
            "学习基础数据类型",
            "掌握控制流语句",
            ...
        ]
        """
```

**Prompt 设计要点**:
- 明确输出格式要求（Python 列表）
- 步骤要具体、可执行
- 使用 ```python 标记便于解析

### 2. Executor (执行器)

```python
class Executor:
    def execute(self, question: str, plan: List[str]) -> str:
        """
        按步骤执行计划

        特点:
        1. 携带历史记录（上下文）
        2. 每个步骤独立调用 LLM
        3. 结果累积传递
        """
```

**执行流程**:
```
步骤 1 → LLM 生成答案 → 记录到历史
步骤 2 → 历史 + 当前步骤 → LLM 生成答案 → 记录到历史
步骤 3 → 历史 + 当前步骤 → LLM 生成答案 → ...
```

### 3. PlanAndSolveAgent (主 Agent)

```python
class PlanAndSolveAgent:
    def run(self, question: str) -> str:
        # Phase 1: 规划
        plan = self.planner.plan(question)

        # Phase 2: 执行
        result = self.executor.execute(question, plan)

        return result
```

## 实际运行效果

**问题**: "帮我制定一个学习 Python 的 3 周计划"

### 规划阶段输出

```
📋 规划阶段
============================================================
问题: 帮我制定一个学习 Python 的 3 周计划

✅ 生成 17 个步骤:
   1. 下载并安装最新版本的 Python 解释器及 VS Code
   2. 编写并运行第一个 'Hello World' 程序
   3. 学习 Python 的基本数据类型
   4. 掌握 Python 的算术运算符
   5. 练习字符串的基本操作
   ...
```

### 执行阶段输出

```
🔨 执行阶段
============================================================

────────────────────────────────────────
📌 步骤 1/17: 下载并安装最新版本的 Python...
────────────────────────────────────────
🧠 调用模型: coding-glm-4.7-free
**1. 安装 Python 解释器**
*   **下载**: 访问 Python 官网下载最新稳定版
*   **安装**: 运行安装程序，勾选 "Add Python to PATH"
*   **验证**: 输入 `python --version` 查看版本

✅ 结果: **1. 安装 Python 解释器**
...

────────────────────────────────────────
📌 步骤 2/17: 编写并运行第一个 'Hello World'...
────────────────────────────────────────
🧠 调用模型: coding-glm-4.7-free
**步骤 2: 编写并运行第一个 'Hello World'**

*   **创建文件**: 打开 VS Code，新建文件保存为 `hello.py`
*   **编写代码**: 输入 `print("Hello World")`
*   **运行程序**: 点击运行按钮或命令行输入 `python hello.py`

✅ 结果: **步骤 2: 编写并运行第一个 'Hello World'**
...
```

## 关键要点

| 要点 | 说明 |
|------|------|
| **解耦设计** | 规划与执行分离，职责清晰 |
| **状态传递** | 历史记录传递上下文，保持连贯性 |
| **逐步执行** | 按规划步骤依次解决，可预测 |
| **格式约束** | 规划输出必须为 Python 列表格式 |

## 适用场景

✅ **适合使用 Plan-and-Solve**:
- 制定学习计划、旅行攻略
- 编写结构化文档（报告、论文）
- 按部就班的问题解决
- 需要整体规划的复杂任务

❌ **不适合使用 Plan-and-Solve**:
- 需要探索试错的问题
- 动态环境交互（如游戏、机器人）
- 需要频繁调整策略的任务
- 外部工具调用（搜索、API）

## 最佳实践

### 1. 规划 Prompt 设计

```python
PLANNER_PROMPT = """
你是一个顶级的 AI 规划专家。请将复杂问题分解为简单、有序的步骤。

要求：
1. 步骤要具体、可执行
2. 步骤之间要有逻辑顺序
3. 输出必须是 Python 列表格式

问题: {question}

请用 ```python 和 ``` 标记输出步骤列表：
```python
["步骤1", "步骤2", "步骤3"]
```
"""
```

### 2. 执行 Prompt 设计

```python
EXECUTOR_PROMPT = """
你是一个顶级的 AI 执行专家。请基于上下文解决当前步骤。

# 原始问题
{question}

# 完整规划
{plan}

# 历史执行记录
{history}

# 当前步骤（请解决此步骤）
{current_step}

要求：
1. 只输出当前步骤的答案
2. 基于历史记录理解上下文
3. 答案要简洁明确
"""
```

### 3. 错误处理

```python
try:
    plan_str = response.split("```python")[1].split("```")[0].strip()
    plan = ast.literal_eval(plan_str)
except Exception as e:
    print(f"解析规划失败: {e}")
    return []
```

## 与 ReAct 的结合

**Plan-and-Solve + ReAct = 更强大的 Agent**

```python
# 第一阶段：Plan-and-Solve 制定整体计划
plan = planner.plan(question)

# 第二阶段：每个步骤用 ReAct 执行
for step in plan:
    # ReAct 处理步骤中的工具调用
    result = react_agent.run(step)
```

这种组合方式适合：
- 复杂任务的整体规划
- 每个步骤中的工具调用
- 灵活与可控的平衡

## 学习检查清单

- [x] 理解 Plan-and-Solve 核心思想
- [x] 理解 Planner 和 Executor 的职责分离
- [x] 理解 Prompt 设计的关键要素
- [x] 能够运行基础示例
- [x] 理解适用场景和局限性
- [ ] 与 ReAct 结合使用
- [ ] 处理实际复杂任务

---

*学习日期: 2026-03-24*
