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
- [x] 接入真实 LLM
- [ ] 添加自定义工具
- [ ] 处理复杂多步任务

---

## 真实 LLM 版本详解

### 文件对比

| 特性 | 模拟版本 (`react_agent.py`) | 真实版本 (`react_agent_real.py`) |
|------|----------------------------|----------------------------------|
| LLM 客户端 | `MockLLM`（预设响应） | `HelloAgentsLLM`（真实 API） |
| 依赖 | 无需外部依赖 | `openai`、`python-dotenv` |
| 配置 | 无需配置 | `.env` 文件配置 API |
| 响应 | 固定、可预测 | 动态生成、真实推理 |
| 输出 | 一次性输出 | 流式输出（实时显示） |

### HelloAgentsLLM 类

```python
class HelloAgentsLLM:
    def __init__(self, model=None, api_key=None, base_url=None):
        # 从 .env 加载配置
        load_dotenv()

        # 支持多服务商：OpenAI/AIHubmix/阿里云
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

    def think(self, messages, temperature=0) -> str:
        # 流式调用 LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True  # 流式输出
        )
        # 实时输出每个 chunk
```

### 多服务商配置

通过 `.env` 文件切换不同 LLM：

```bash
# AIHubmix（当前使用，有免费额度）
LLM_API_KEY=sk-xxx
LLM_MODEL_ID=coding-glm-4.7-free
LLM_BASE_URL=https://aihubmix.com/v1

# OpenAI 官方
LLM_API_KEY=sk-xxx
LLM_MODEL_ID=gpt-3.5-turbo
LLM_BASE_URL=https://api.openai.com/v1

# 阿里云百炼
LLM_API_KEY=sk-xxx
LLM_MODEL_ID=qwen-turbo
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 实际运行效果

```
🚀 ReAct Agent - 真实 LLM 版本
============================================================
📋 环境检查:
   LLM_API_KEY: ✅ 已设置
   LLM_MODEL_ID: coding-glm-4.7-free

🔌 连接 LLM...
   模型: coding-glm-4.7-free

📝 请输入问题: 计算 25 * 4 + 100 等于多少？

============================================================
🎯 问题: 计算 25 * 4 + 100 等于多少？
============================================================

────────────────────────────────────────
📍 步骤 1/5
────────────────────────────────────────
🧠 调用模型: coding-glm-4.7-free
我需要先计算 25 * 4。Thought: 我需要先计算 25 * 4。

Action: Calculator[25 * 4]

🤔 Thought:
我需要先计算 25 * 4。
🎬 Action: Calculator[25 * 4]
🔧 执行计算器: 25 * 4
👀 Observation: 100

────────────────────────────────────────
📍 步骤 2/5
────────────────────────────────────────
🧠 调用模型: coding-glm-4.7-free
现在计算 100 + 100。Thought: 现在计算 100 + 100。

Action: Calculator[100 + 100]

🤔 Thought:
现在计算 100 + 100。
🎬 Action: Calculator[100 + 100]
🔧 执行计算器: 100 + 100
👀 Observation: 200

────────────────────────────────────────
📍 步骤 3/5
────────────────────────────────────────
🧠 调用模型: coding-glm-4.7-free
最终结果是 200。Thought: 最终结果是 200。

Action: Finish[200]

🤔 Thought:
最终结果是 200。

============================================================
🎉 最终答案: 200
============================================================
```

### 关键改进点

1. **流式输出** - `stream=True` 实现实时显示，提升用户体验
2. **环境隔离** - `.env` 管理密钥，`.gitignore` 保护不上传
3. **交互模式** - 支持连续提问，无需重启程序
4. **错误处理** - API 失败时优雅退出并提示
5. **多服务商** - 一份代码支持 OpenAI/AIHubmix/阿里云等

### 扩展自定义工具

```python
# 1. 定义工具函数
def search(query: str) -> str:
    """搜索工具"""
    return f"搜索结果: {query}"

# 2. 注册到 ToolExecutor
tools.register(
    "Search",
    "网页搜索，如 Search[Python教程]",
    search
)

# 3. Agent 自动学会使用
# LLM 会根据描述理解工具用途并调用
```

### 安全注意事项

- ✅ API 密钥存储在 `.env`，已添加 `.gitignore`
- ⚠️ 不要将 `.env` 文件内容分享到公开场合
- ⚠️ 定期轮换 API 密钥
- ✅ 使用免费额度服务（如 AIHubmix）进行学习测试

---

## 自定义工具实战

### 已实现的工具列表

| 工具名 | 功能 | 示例用法 | 安全特性 |
|--------|------|----------|----------|
| **Calculator** | 数学计算 | `Calculator[25 * 4]` | 字符白名单过滤 |
| **Weather** | 天气查询 | `Weather[北京]` | 模拟数据 |
| **CurrentTime** | 获取当前时间 | `CurrentTime[now]` | - |
| **FileReader** | 读取文件 | `FileReader[README.md]` | 禁止敏感路径、大小限制 |
| **WebSearch** | 网页搜索 | `WebSearch[Python教程]` | 模拟数据 |
| **PythonRunner** | 执行 Python 代码 | `PythonRunner[print(2+3)]` | 危险代码过滤、受限环境 |

### 工具测试记录

#### 1. CurrentTime 工具

**问题**: "现在几点了？"

```
📍 步骤 1/5
🧠 调用模型: coding-glm-4.7-free
🤔 Thought: 用户询问现在几点了，需要获取当前时间信息
🎬 Action: CurrentTime[now]
🔧 获取当前时间
👀 Observation: 2026-03-24 23:12:30

📍 步骤 2/5
🤔 Thought: 已经获取到当前时间为 2026-03-24 23:12:30，可以直接回答用户
🎉 最终答案: 现在是 2026年3月24日 23点12分30秒
```

#### 2. WebSearch 工具

**问题**: "搜索一下 Python 是什么"

```
📍 步骤 1/5
🧠 调用模型: coding-glm-4.7-free
🤔 Thought: 用户想要了解 Python 是什么，我需要使用网页搜索工具
🎬 Action: WebSearch[Python是什么]
🔧 搜索: Python是什么
👀 Observation: 搜索结果: Python 是一种流行的编程语言...

📍 步骤 2/5
🤔 Thought: 已经通过 WebSearch 获取到了 Python 的相关信息
🎉 最终答案: Python 是一种流行的编程语言，由 Guido van Rossum 于 1991 年创建...
```

#### 3. PythonRunner 工具

**问题**: "执行 Python 代码计算 2 的 10 次方"

```
📍 步骤 1/5
🧠 调用模型: coding-glm-4.7-free
🤔 Thought: 用户要求执行 Python 代码计算 2 的 10 次方
🎬 Action: PythonRunner[2**10]
🔧 执行 Python 代码: 2**10
👀 Observation: 执行成功（无输出）

📍 步骤 2/5
🧠 调用模型: coding-glm-4.7-free
🤔 Thought: 上一步执行了 2**10，但没有使用 print 函数，所以没有输出
🎬 Action: PythonRunner[print(2**10)]
🔧 执行 Python 代码: print(2**10)
👀 Observation: 执行结果:\n1024

🎉 最终答案: 2 的 10 次方等于 1024
```

**关键观察**: LLM 能够从第一次无输出中**自我反思**，自动修正代码添加 `print()`，体现了 ReAct 的迭代优化能力。

### 添加新工具的步骤

```python
# 步骤 1: 定义工具函数
def my_tool(input_str: str) -> str:
    """
    工具描述，会被放入 Prompt 中让 LLM 理解
    """
    # 实现工具逻辑
    result = process(input_str)
    return f"结果: {result}"

# 步骤 2: 注册到 ToolExecutor
tools.register(
    "MyTool",           # 工具名称（大写驼峰）
    "工具功能描述",      # 描述（LLM 通过此描述选择工具）
    my_tool             # 函数
)

# 步骤 3: Agent 自动学会使用
# LLM 会根据工具描述，在需要时自动调用 MyTool[input]
```

### 工具设计最佳实践

1. **明确的描述**: 让 LLM 理解工具用途和参数格式
2. **参数简洁**: 单个字符串输入，复杂数据用 JSON
3. **错误处理**: 返回清晰的错误信息而非抛出异常
4. **安全限制**:
   - 文件操作限制路径和大小
   - 代码执行过滤危险关键字
   - 网络请求设置超时
5. **输出格式**: 统一格式便于 LLM 理解

---

## 学习检查清单（更新）

- [x] 理解 ReAct 核心循环
- [x] 理解 ToolExecutor 的作用
- [x] 理解 Prompt 如何约束 LLM 输出
- [x] 能够运行基础示例
- [x] 接入真实 LLM
- [x] **添加自定义工具** ✅ 已完成
- [x] **测试多工具协作** ✅ 已完成
- [ ] 处理复杂多步任务

---

*学习日期: 2026-03-24*
