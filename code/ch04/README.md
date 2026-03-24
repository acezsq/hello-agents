# Chapter 4: Agent 经典范式实现

本章实现了三种经典的 Agent 架构范式：ReAct、Plan-and-Solve、Reflection

## 文件说明

| 文件 | 范式 | 说明 |
|------|------|------|
| `react_agent.py` | ReAct | 模拟 LLM 版本（无需 API） |
| `react_agent_real.py` | ReAct | 真实 LLM 版本（需要 API） |
| `plan_and_solve_agent.py` | Plan-and-Solve | 先规划后执行范式 |
| `.env.example` | - | 环境变量配置模板 |

---

## 范式对比

| 范式 | 核心策略 | 最佳适用场景 |
|------|----------|--------------|
| **ReAct** | Think-Act-Observe 循环 | 外部工具调用、动态环境交互 |
| **Plan-and-Solve** | 先规划，后执行 | 结构化、多步骤推理任务 |
| **Reflection** | Execute-Reflect-Refine | 质量要求高、可迭代优化 |

## 快速开始

### 1. 运行演示版本（无需 API）

```bash
python react_agent.py
```

这个版本使用 MockLLM 模拟响应，展示 ReAct 的工作流程。

### 2. 运行真实 LLM 版本

#### 2.1 安装依赖

```bash
pip install openai python-dotenv
```

#### 2.2 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 密钥
```

#### 2.3 运行

```bash
python react_agent_real.py
```

## 支持的 LLM 服务商

| 服务商 | 模型示例 | BASE_URL |
|--------|----------|----------|
| OpenAI | gpt-3.5-turbo, gpt-4 | https://api.openai.com/v1 |
| 阿里云百炼 | qwen-turbo, qwen-max | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 其他 | - | OpenAI 兼容格式 |

## ReAct 核心概念

**循环流程**: Thought → Action → Observation

1. **Thought**: LLM 分析当前情况，决定下一步
2. **Action**: 调用工具或结束任务
3. **Observation**: 获取工具执行结果
4. 重复直到获得最终答案

## 已集成的工具

### 基础工具

| 工具 | 功能 | 示例 |
|------|------|------|
| `Calculator` | 数学计算器 | `Calculator[25 * 4 + 100]` |
| `Weather` | 天气查询（模拟数据） | `Weather[北京]` |

### 自定义工具

| 工具 | 功能 | 示例 | 安全特性 |
|------|------|------|----------|
| `CurrentTime` | 获取当前时间 | `CurrentTime[now]` | - |
| `FileReader` | 读取项目目录下的文件 | `FileReader[README.md]` | 禁止敏感路径、大小限制 100KB |
| `WebSearch` | 网页搜索（模拟数据） | `WebSearch[Python教程]` | - |
| `PythonRunner` | 安全执行 Python 代码 | `PythonRunner[print(2+3)]` | 危险代码过滤、受限环境 |

## 使用示例

### ReAct Agent

启动后，可以输入以下问题测试：

```
# 基础工具
计算 125 * 8 + 500 等于多少？
北京和上海哪个城市今天更暖和？

# 自定义工具
现在几点了？
搜索一下 Python 是什么
执行 Python 代码计算 2 的 10 次方
帮我读取 README.md 文件内容
```

### Plan-and-Solve Agent

适合需要**整体规划**的任务：

```bash
python plan_and_solve_agent.py
```

**示例问题**:

```
帮我制定一个学习 Python 的 4 周计划
如何准备一次技术面试？
写一份上海三日游攻略
解释什么是机器学习，并举例说明应用场景
```

**特点**:
- 先规划：生成有序的步骤列表
- 后执行：逐个步骤详细解答
- 适合：学习计划、攻略制定、结构化文档

## 自定义工具

```python
def my_tool(input: str) -> str:
    """工具函数"""
    return f"处理结果: {input}"

# 注册工具
tools.register("MyTool", "工具描述", my_tool)
```

## 学习资源

- [ReAct 学习总结](../../notes/ch04-react-summary.md)
- [Plan-and-Solve 学习总结](../../notes/ch04-plan-and-solve-summary.md)
- [官方教程](https://datawhalechina.github.io/hello-agents/#/./chapter4/)
