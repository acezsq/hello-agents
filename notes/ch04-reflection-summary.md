# Reflection 学习总结

## 什么是 Reflection？

**Reflection = 执行(Execute) + 反思(Reflect) + 优化(Refine)**

一种通过自我反思不断改进输出质量的架构范式。

## 核心思想

**迭代优化循环**:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   初始执行   │────→│   反思审查   │────→│   优化改进   │
│  (Execute)  │     │  (Reflect)  │     │  (Refine)   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
        ↑───────────────────┘                  │
        └──────────────────────────────────────┘
                    （循环直到收敛）
```

## 与 ReAct、Plan-and-Solve 的区别

| 特性 | Reflection | ReAct | Plan-and-Solve |
|------|------------|-------|----------------|
| **核心策略** | 执行-反思-优化循环 | 思考-行动-观察循环 | 先规划后执行 |
| **迭代方式** | 同一任务多次迭代优化 | 不同步骤推进 | 固定步骤执行 |
| **适用场景** | 质量要求高的输出 | 工具调用、交互 | 结构化任务 |
| **输出改进** | 基于反馈自我优化 | 基于观察调整 | 按规划执行 |

## 代码结构

```
reflection_agent.py
├── HelloAgentsLLM    # LLM 客户端（复用）
├── Memory            # 记忆模块 - 记录执行和反思历史
├── INITIAL_PROMPT    # 初始执行 Prompt
├── REFLECT_PROMPT    # 反思审查 Prompt
├── REFINE_PROMPT     # 优化改进 Prompt
└── ReflectionAgent   # 主 Agent - 协调迭代优化
```

## 核心组件详解

### 1. Memory (记忆模块)

```python
class Memory:
    """记录执行和反思的历史"""

    def add_record(self, record_type: str, content: str):
        # record_type: 'execution' 或 'reflection'
        self.records.append({"type": record_type, "content": content})

    def get_last_execution(self) -> str:
        # 获取最后一次执行结果

    def get_trajectory(self) -> str:
        # 获取完整的优化轨迹
```

**作用**：保存每次迭代的结果，便于追踪改进过程。

### 2. 三个 Prompt 模板

#### INITIAL_PROMPT - 初始执行
```
你是一个专家级助手。请完成以下任务：
任务: {task}
要求：
1. 给出完整的解决方案
2. 确保内容准确、专业
直接输出结果：
```

#### REFLECT_PROMPT - 反思审查
```
你是一个非常严格的评审专家。

任务: {task}
当前版本内容: {content}

请从以下维度评估：
1. 准确性：是否有错误或遗漏？
2. 完整性：是否覆盖了所有要求？
3. 清晰度：表达是否清晰易懂？
4. 优化空间：是否有更好的实现方式？

如果内容已经很好，说"无需改进"。
```

#### REFINE_PROMPT - 优化改进
```
你是一个乐于改进的专家。

任务: {task}
上一版内容: {last_content}
评审反馈: {feedback}

请根据反馈优化：
1. 修复指出的问题
2. 采纳改进建议
3. 保持原有优点

直接输出优化后的结果：
```

### 3. ReflectionAgent 核心循环

```python
def run(self, task: str) -> str:
    # 1. 初始执行
    content = generate_initial(task)

    for i in range(max_iterations):
        # 2. 反思审查
        feedback = reflect(task, content)

        # 3. 检查收敛
        if "no improvement needed" in feedback:
            break  # 已最优，停止迭代

        # 4. 优化改进
        content = refine(task, content, feedback)

    return content
```

## 关键要点

| 要点 | 说明 |
|------|------|
| **迭代优化** | 多轮执行-反思-优化，逐步提升质量 |
| **收敛判断** | 当反馈为"无需改进"时停止，避免无限循环 |
| **记忆管理** | 记录所有版本，可追溯优化过程 |
| **质量导向** | 专注于输出质量，而非任务完成速度 |

## 适用场景

✅ **适合使用 Reflection**：
- 代码生成与优化
- 文章/报告撰写
- 创意内容生成（诗歌、故事）
- 需要高质量输出的任务

❌ **不适合使用 Reflection**：
- 实时交互任务
- 需要快速响应的场景
- 一次性简单任务
- 成本敏感的场景（迭代会增加 API 调用）

## 实际运行效果

**任务**: "写一个 Python 函数，计算斐波那契数列的第 n 项"

### 第一轮：初始生成

```
📝 Phase 1: 初始生成

🧠 调用模型: coding-glm-4.7-free
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

✅ 第 1 版完成（156 字符）
```

### 第二轮：反思审查

```
🔍 Phase 2.1: 反思审查

🧠 调用模型: coding-glm-4.7-free
评审意见：
1. 使用递归实现，时间复杂度为 O(2^n)，效率较低
2. 没有处理大数溢出问题
3. 建议改用动态规划或迭代方式，时间复杂度可优化至 O(n)
4. 建议添加文档字符串和类型注解
```

### 第三轮：优化改进

```
✨ Phase 2.1: 优化改进

🧠 调用模型: coding-glm-4.7-free
def fibonacci(n: int) -> int:
    """
    计算斐波那契数列的第 n 项

    Args:
        n: 项数（从0开始）

    Returns:
        第 n 项的值
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

✅ 第 2 版完成（312 字符）
```

**优化效果**：
- 时间复杂度：O(2ⁿ) → O(n)
- 增加了文档字符串
- 添加了类型注解
- 避免了递归栈溢出

## 最佳实践

### 1. 设计好的反思 Prompt

```python
REFLECT_PROMPT = """
你是一个非常严格的评审专家...

评估维度：
1. 准确性：是否有错误？
2. 完整性：是否覆盖所有要求？
3. 清晰度：表达是否清晰？
4. 优化空间：是否有更好方式？

如果已经很好，直接说"无需改进"。
"""
```

### 2. 设置合理的最大迭代次数

```python
agent = ReflectionAgent(llm, max_iterations=3)
```

- 太少：优化不充分
- 太多：成本增加，可能过拟合
- 通常 2-3 次足够

### 3. 清晰的收敛判断

```python
def _is_converged(self, feedback: str) -> bool:
    indicators = [
        "no improvement needed",
        "无需改进",
        "已经很完美"
    ]
    return any(indicator in feedback.lower()
               for indicator in indicators)
```

## 三种范式的选择指南

| 场景 | 推荐范式 | 原因 |
|------|----------|------|
| 需要调用搜索/API | **ReAct** | 工具调用能力强 |
| 制定计划/攻略 | **Plan-and-Solve** | 结构化思考 |
| 代码/文章优化 | **Reflection** | 迭代提升质量 |
| 探索性任务 | **ReAct** | 灵活应变 |
| 质量要求极高 | **Reflection** | 多次优化 |

## 学习检查清单

- [x] 理解 Reflection 核心思想
- [x] 理解 Memory 模块的作用
- [x] 理解三个 Prompt 的分工
- [x] 理解迭代优化的流程
- [x] 能够区分三种范式的适用场景
- [ ] 组合使用多种范式
- [ ] 应用到实际项目

---

*学习日期: 2026-03-25*
