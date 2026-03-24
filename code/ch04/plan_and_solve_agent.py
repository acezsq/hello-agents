"""
Plan-and-Solve Agent 实现
先规划(Plan)，后执行(Solve) 的两阶段范式
"""

import os
import ast
from typing import List, Dict
from dotenv import load_dotenv

# 尝试导入 openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  未安装 openai，请先运行: pip install openai python-dotenv")


# ============ 1. LLM Client (复用 ReAct 版本的) ============

class HelloAgentsLLM:
    """LLM 客户端 - 支持 OpenAI 格式 API"""

    def __init__(self, model=None, api_key=None, base_url=None, timeout=None):
        if not OPENAI_AVAILABLE:
            raise ImportError("请先安装 openai: pip install openai")

        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()

        self.model = model or os.getenv("LLM_MODEL_ID", "gpt-3.5-turbo")
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))

        if not api_key:
            raise ValueError("未设置 LLM_API_KEY，请检查 .env 文件")

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature=0) -> str:
        """调用 LLM 获取响应"""
        print(f"🧠 调用模型: {self.model}")

        try:
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
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            raise


# ============ 2. Planner (规划器) ============

PLANNER_PROMPT_TEMPLATE = """你是一个顶级的 AI 规划专家。请将复杂问题分解为简单、有序的步骤。

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


class Planner:
    """规划器 - 将复杂问题分解为步骤"""

    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm = llm_client

    def plan(self, question: str) -> List[str]:
        """
        规划步骤

        Args:
            question: 用户问题

        Returns:
            步骤列表，如 ["步骤1", "步骤2", "步骤3"]
        """
        print(f"\n{'='*60}")
        print("📋 规划阶段")
        print(f"{'='*60}")
        print(f"问题: {question}\n")

        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        response = self.llm.think([{"role": "user", "content": prompt}])

        try:
            # 解析 Python 列表格式
            if "```python" in response:
                plan_str = response.split("```python")[1].split("```")[0].strip()
            elif "```" in response:
                plan_str = response.split("```")[1].strip()
            else:
                plan_str = response.strip()

            plan = ast.literal_eval(plan_str)

            if not isinstance(plan, list):
                raise ValueError("解析结果不是列表")

            print(f"\n✅ 生成 {len(plan)} 个步骤:")
            for i, step in enumerate(plan, 1):
                print(f"   {i}. {step}")

            return plan

        except Exception as e:
            print(f"❌ 解析规划失败: {e}")
            print(f"原始响应: {response[:200]}...")
            return []


# ============ 3. Executor (执行器) ============

EXECUTOR_PROMPT_TEMPLATE = """你是一个顶级的 AI 执行专家。请基于上下文解决当前步骤。

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

当前步骤答案：
"""


class Executor:
    """执行器 - 按步骤执行计划"""

    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm = llm_client

    def execute(self, question: str, plan: List[str]) -> str:
        """
        执行规划

        Args:
            question: 原始问题
            plan: 步骤列表

        Returns:
            最终答案
        """
        print(f"\n{'='*60}")
        print("🔨 执行阶段")
        print(f"{'='*60}\n")

        history = []
        final_result = ""

        for i, step in enumerate(plan, 1):
            print(f"\n{'─'*50}")
            print(f"📌 步骤 {i}/{len(plan)}: {step}")
            print(f"{'─'*50}")

            # 构建执行 Prompt
            history_str = "\n".join(history) if history else "（无）"
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan="\n".join([f"{j+1}. {s}" for j, s in enumerate(plan)]),
                history=history_str,
                current_step=step
            )

            # 调用 LLM 执行当前步骤
            result = self.llm.think([{"role": "user", "content": prompt}])

            print(f"\n✅ 结果: {result[:200]}{'...' if len(result) > 200 else ''}")

            # 记录历史
            history.append(f"步骤 {i}: {step}")
            history.append(f"结果: {result}")
            history.append("")

            final_result = result

        print(f"\n{'='*60}")
        print("🎉 执行完成")
        print(f"{'='*60}")

        return final_result


# ============ 4. Plan-and-Solve Agent ============

class PlanAndSolveAgent:
    """
    Plan-and-Solve Agent

    两阶段工作流：
    1. Planning: 将复杂问题分解为有序的步骤列表
    2. Execution: 按步骤依次执行，携带上下文
    """

    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def run(self, question: str) -> str:
        """
        运行 Plan-and-Solve Agent

        Args:
            question: 用户问题

        Returns:
            最终答案
        """
        print(f"\n🚀 Plan-and-Solve Agent")
        print(f"模型: {self.llm.model}")

        # Phase 1: 规划
        plan = self.planner.plan(question)
        if not plan:
            print("❌ 规划失败")
            return None

        # Phase 2: 执行
        result = self.executor.execute(question, plan)

        return result


# ============ 5. 测试示例 ============

def main():
    """主函数 - 演示 Plan-and-Solve Agent"""

    print("🚀 Plan-and-Solve Agent 演示")
    print("=" * 60)
    print()

    # 检查环境
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("❌ 请先配置 .env 文件")
        return

    try:
        # 创建 LLM 客户端
        llm = HelloAgentsLLM()
        print(f"✅ 连接成功: {llm.model}\n")

        # 创建 Agent
        agent = PlanAndSolveAgent(llm)

        # 测试示例
        examples = [
            "帮我制定一个学习 Python 的 4 周计划",
            "如何准备一次技术面试？",
            "写一份上海三日游攻略",
            "解释什么是机器学习，并举例说明应用场景",
        ]

        print("📚 示例问题:")
        for i, ex in enumerate(examples, 1):
            print(f"   {i}. {ex}")
        print()

        # 交互式运行
        while True:
            try:
                question = input("\n📝 请输入问题 (quit 退出): ").strip()
                if question.lower() in ('quit', 'exit', 'q'):
                    break
                if not question:
                    continue

                agent.run(question)

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")


if __name__ == "__main__":
    main()
