# 第4章：智能体经典范式构建

> 官方教程：https://datawhalechina.github.io/hello-agents/#/./chapter4/第四章%20智能体经典范式构建
> GitHub 源文件：https://github.com/datawhalechina/Hello-Agents/blob/main/docs/chapter4/Chapter4-Building-Classic-Agent-Paradigms.md

## 本章目标

- 掌握 Agent 的三个经典架构范式：ReAct、Plan-and-Solve、Reflection
- 理解每种范式的核心思想和适用场景
- 学会实现基础的 Agent 系统

---

## 4.1 环境准备

### 依赖安装

```bash
pip install openai python-dotenv
```

### API 配置 (.env)

```bash
LLM_API_KEY="YOUR-API-KEY"
LLM_MODEL_ID="YOUR-MODEL"
LLM_BASE_URL="YOUR-URL"
```

### LLM Client 封装类

```python
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class HelloAgentsLLM:
    def __init__(self, model=None, apiKey=None, baseUrl=None, timeout=None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature=0) -> str:
        print(f"🧠 Calling {self.model} model...")
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature, stream=True
        )
        collected = []
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            collected.append(content)
        print()
        return "".join(collected)
```

---

## 4.2 ReAct (Reasoning + Acting)

### 核心思想

**Think-Act-Observe 循环**：交替进行推理(Thought)和行动(Action)，根据观察结果(Observation)决定下一步。

工作流程：**Thought → Action → Observation → Thought → ...**

### 工具实现示例

```python
from serpapi import SerpApiClient

def search(query: str) -> str:
    """SerpApi 搜索工具"""
    print(f"🔍 Executing [SerpApi] web search: {query}")
    api_key = os.getenv("SERPAPI_API_KEY")
    params = {
        "engine": "google", "q": query, "api_key": api_key,
        "gl": "cn", "hl": "zh-cn"
    }
    client = SerpApiClient(params)
    results = client.get_dict()

    # 解析搜索结果
    if "answer_box" in results and "answer" in results["answer_box"]:
        return results["answer_box"]["answer"]
    if "knowledge_graph" in results:
        return results["knowledge_graph"]["description"]
    if "organic_results" in results:
        snippets = [f"[{i+1}] {r.get('title')}\n{r.get('snippet')}"
                   for i, r in enumerate(results["organic_results"][:3])]
        return "\n\n".join(snippets)
    return f"No info found for '{query}'"
```

### 工具执行器

```python
class ToolExecutor:
    def __init__(self):
        self.tools = {}

    def registerTool(self, name: str, description: str, func: callable):
        self.tools[name] = {"description": description, "func": func}

    def getTool(self, name: str) -> callable:
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        return "\n".join([f"- {n}: {i['description']}" for n, i in self.tools.items()])
```

### ReAct Prompt 模板

```python
REACT_PROMPT_TEMPLATE = """
You are an intelligent assistant capable of calling external tools.

Available tools:
{tools}

Respond strictly in this format:
Thought: Your thinking process to analyze and plan.
Action: One of:
- {{tool_name}}[{{tool_input}}]`: Call a tool
- `Finish[final answer]`: When you have the answer

Question: {question}
History: {history}
"""
```

### ReAct Agent 实现

```python
import re

class ReActAgent:
    def __init__(self, llm_client, tool_executor, max_steps=5):
        self.llm = llm_client
        self.tools = tool_executor
        self.max_steps = max_steps
        self.history = []

    def _parse_output(self, text: str):
        thought = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        return (thought.group(1).strip() if thought else None,
                action.group(1).strip() if action else None)

    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def run(self, question: str):
        self.history = []
        for step in range(1, self.max_steps + 1):
            print(f"--- Step {step} ---")

            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=self.tools.getAvailableTools(),
                question=question,
                history="\n".join(self.history)
            )

            response = self.llm.think([{"role": "user", "content": prompt}])
            thought, action = self._parse_output(response)

            if thought:
                print(f"🤔 Thought: {thought}")
            if not action:
                break

            if action.startswith("Finish"):
                answer = re.match(r"Finish\[(.*)\]", action).group(1)
                print(f"🎉 Final Answer: {answer}")
                return answer

            tool_name, tool_input = self._parse_action(action)
            print(f"🎬 Action: {tool_name}[{tool_input}]")

            tool_func = self.tools.getTool(tool_name)
            observation = tool_func(tool_input) if tool_func else f"Error: Tool '{tool_name}' not found"
            print(f"👀 Observation: {observation[:200]}...")

            self.history.extend([f"Action: {action}", f"Observation: {observation}"])

        return None
```

### 关键要点

- **循环执行**：最多执行 `max_steps` 步
- **格式约束**：严格遵循 `Thought:` 和 `Action:` 格式
- **工具调用**：通过 `ToolName[input]` 语法调用
- **终止条件**：输出 `Finish[answer]` 结束

---

## 4.3 Plan-and-Solve

### 核心思想

**两阶段工作流**：先规划(Plan)，再执行(Solve)。

适合结构化、多步骤的复杂任务。

### Planner（规划器）

```python
PLANNER_PROMPT_TEMPLATE = """
You are a top AI planning expert. Decompose complex problems into simple, ordered steps.
Output must be a Python list format.

Question: {question}

Output with ```python and ``` markers:
```python
["Step 1", "Step 2", "Step 3"]
```
"""

class Planner:
    def __init__(self, llm_client):
        self.llm = llm_client

    def plan(self, question: str) -> list:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        response = self.llm.think([{"role": "user", "content": prompt}])

        try:
            plan_str = response.split("```python")[1].split("```")[0].strip()
            return ast.literal_eval(plan_str)
        except Exception as e:
            print(f"Parse error: {e}")
            return []
```

### Executor（执行器）

```python
EXECUTOR_PROMPT_TEMPLATE = """
You are a top AI execution expert. Solve the current step based on context.

# Original Question: {question}
# Complete Plan: {plan}
# History: {history}
# Current Step: {current_step}

Output only the answer for this step.
"""

class Executor:
    def __init__(self, llm_client):
        self.llm = llm_client

    def execute(self, question: str, plan: list) -> str:
        history = ""
        for i, step in enumerate(plan):
            print(f"\n-> Step {i+1}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history or "None", current_step=step
            )
            result = self.llm.think([{"role": "user", "content": prompt}])
            history += f"Step {i+1}: {step}\nResult: {result}\n\n"
            print(f"✅ Result: {result}")
        return result
```

### Plan-and-Solve Agent

```python
class PlanAndSolveAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def run(self, question: str):
        print(f"Question: {question}")
        plan = self.planner.plan(question)
        if not plan:
            return None
        return self.executor.execute(question, plan)
```

### 关键要点

- **解耦设计**：规划与执行分离
- **状态传递**：历史记录传递上下文
- **逐步执行**：按规划步骤依次解决

---

## 4.4 Reflection（自我反思）

### 核心思想

**执行-反思-优化循环**：生成初版结果 → 反思问题 → 优化改进。

适合对质量要求高、可迭代优化的任务。

### Memory（记忆模块）

```python
class Memory:
    def __init__(self):
        self.records = []

    def add_record(self, record_type: str, content: str):
        """record_type: 'execution' 或 'reflection'"""
        self.records.append({"type": record_type, "content": content})

    def get_trajectory(self) -> str:
        parts = []
        for r in self.records:
            label = "Previous Attempt" if r['type'] == 'execution' else "Reviewer Feedback"
            parts.append(f"--- {label} ---\n{r['content']}")
        return "\n\n".join(parts)

    def get_last_execution(self):
        for r in reversed(self.records):
            if r['type'] == 'execution':
                return r['content']
        return None
```

### Prompt 模板

```python
INITIAL_PROMPT = """You are a senior Python programmer. Write code for: {task}"""

REFLECT_PROMPT = """You are an extremely strict code review expert focused on algorithm efficiency.
Review this code and suggest improvements or say 'no improvement needed'.

Task: {task}
Code: {code}"""

REFINE_PROMPT = """Optimize your code based on reviewer feedback.

Task: {task}
Previous code: {last_code}
Feedback: {feedback}

Output optimized code only."""
```

### Reflection Agent

```python
class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm = llm_client
        self.memory = Memory()
        self.max_iter = max_iterations

    def _get_response(self, prompt: str) -> str:
        return self.llm.think([{"role": "user", "content": prompt}])

    def run(self, task: str):
        # 初始执行
        code = self._get_response(INITIAL_PROMPT.format(task=task))
        self.memory.add_record("execution", code)

        for i in range(self.max_iter):
            # 反思
            feedback = self._get_response(REFLECT_PROMPT.format(
                task=task, code=self.memory.get_last_execution()
            ))
            self.memory.add_record("reflection", feedback)

            if "no improvement needed" in feedback.lower():
                print("✅ Converged")
                break

            # 优化
            code = self._get_response(REFINE_PROMPT.format(
                task=task,
                last_code=self.memory.get_last_execution(),
                feedback=feedback
            ))
            self.memory.add_record("execution", code)

        return self.memory.get_last_execution()
```

### 关键要点

- **迭代优化**：多轮执行-反思-优化
- **收敛判断**：当反馈为 "no improvement needed" 时停止
- **记忆管理**：记录每次执行和反思结果

---

## 4.5 三种范式对比

| 范式 | 核心策略 | 最佳适用场景 |
|------|----------|--------------|
| **ReAct** | Think-Act-Observe 循环 | 外部工具调用、动态环境交互 |
| **Plan-and-Solve** | 先规划，后执行 | 结构化、多步骤推理任务 |
| **Reflection** | Execute-Reflect-Refine | 质量要求高、可迭代优化 |

### 如何选择？

1. **需要调用搜索/API 等工具** → 选 **ReAct**
2. **任务可分解为固定步骤** → 选 **Plan-and-Solve**
3. **需要高质量输出（如代码）** → 选 **Reflection**

---

## 本章小结

**核心收获**：

1. ReAct：通过交替推理和行动与外部世界交互
2. Plan-and-Solve：将复杂任务分解规划后逐步执行
3. Reflection：通过自我反思不断优化输出质量

**代码实践**：见 [code/ch04/](../code/ch04/)

---

## 参考资源

- 官方教程：https://datawhalechina.github.io/hello-agents/#/./chapter4/
- 本章源码：https://github.com/datawhalechina/Hello-Agents/tree/main/docs/chapter4

---
*学习日期：*
