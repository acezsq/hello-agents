"""
Reflection Agent 实现
执行-反思-优化循环范式
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# 尝试导入 openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  未安装 openai，请先运行: pip install openai python-dotenv")


# ============ 1. LLM Client (复用之前的) ============

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


# ============ 2. Memory (记忆模块) ============

class Memory:
    """
    记忆模块 - 记录执行和反思的历史

    记录两种类型的内容：
    - 'execution': 生成的结果（代码、文章等）
    - 'reflection': 反思反馈（改进建议）
    """

    def __init__(self):
        self.records = []

    def add_record(self, record_type: str, content: str):
        """
        添加记录

        Args:
            record_type: 'execution' 或 'reflection'
            content: 记录内容
        """
        self.records.append({
            "type": record_type,
            "content": content,
            "iteration": len([r for r in self.records if r['type'] == record_type]) + 1
        })

    def get_trajectory(self) -> str:
        """
        获取完整的执行轨迹

        Returns:
            格式化的历史记录字符串
        """
        parts = []
        for r in self.records:
            if r['type'] == 'execution':
                label = f"📝 第 {r['iteration']} 版输出"
            else:
                label = f"🔍 第 {r['iteration']} 轮反思"
            parts.append(f"--- {label} ---\n{r['content']}")
        return "\n\n".join(parts)

    def get_last_execution(self) -> str:
        """获取最后一次执行结果"""
        for r in reversed(self.records):
            if r['type'] == 'execution':
                return r['content']
        return None

    def get_last_reflection(self) -> str:
        """获取最后一次反思结果"""
        for r in reversed(self.records):
            if r['type'] == 'reflection':
                return r['content']
        return None

    def get_iteration_count(self) -> int:
        """获取迭代次数"""
        return len([r for r in self.records if r['type'] == 'execution'])


# ============ 3. Prompt 模板 ============

# 初始执行 Prompt - 生成第一版结果
INITIAL_PROMPT = """你是一个专家级助手。请完成以下任务：

任务: {task}

要求：
1. 给出完整的解决方案
2. 确保内容准确、专业
3. 如果是代码，确保可以运行

直接输出结果，不需要解释过程：
"""

# 反思 Prompt - 审查并找出问题
REFLECT_PROMPT = """你是一个非常严格的评审专家，专注于质量审查和改进建议。

任务: {task}

当前版本内容:
```
{content}
```

请仔细审查上述内容，从以下维度评估：
1. 准确性：是否有错误或遗漏？
2. 完整性：是否覆盖了所有要求？
3. 清晰度：表达是否清晰易懂？
4. 优化空间：是否有更好的实现方式？

如果发现可以改进的地方，请具体说明：
- 问题在哪里
- 如何改进
- 改进后的预期效果

如果内容已经很好，不需要改进，请直接说："无需改进"（no improvement needed）

评审意见：
"""

# 优化 Prompt - 根据反馈改进
REFINE_PROMPT = """你是一个乐于改进的专家。请根据评审反馈优化你的输出。

任务: {task}

上一版内容:
```
{last_content}
```

评审反馈:
```
{feedback}
```

请根据反馈优化内容：
1. 修复指出的问题
2. 采纳改进建议
3. 保持原有优点

直接输出优化后的完整结果：
"""


# ============ 4. Reflection Agent ============

class ReflectionAgent:
    """
    Reflection Agent - 自我反思优化范式

    核心循环：执行 → 反思 → 优化 → （重复直到收敛）

    Attributes:
        llm: LLM 客户端
        memory: 记忆模块，记录所有迭代
        max_iter: 最大迭代次数，防止无限循环
    """

    def __init__(self, llm_client: HelloAgentsLLM, max_iterations=3):
        self.llm = llm_client
        self.memory = Memory()
        self.max_iter = max_iterations

    def _get_response(self, prompt: str, temperature=0) -> str:
        """内部方法：调用 LLM"""
        return self.llm.think([{"role": "user", "content": prompt}], temperature)

    def _is_converged(self, feedback: str) -> bool:
        """判断是否收敛（无需进一步改进）"""
        indicators = [
            "no improvement needed",
            "无需改进",
            "已经很完美",
            "没有明显问题",
            "非常满意",
            "无法进一步优化"
        ]
        feedback_lower = feedback.lower()
        return any(indicator in feedback_lower for indicator in indicators)

    def run(self, task: str) -> str:
        """
        运行 Reflection Agent

        Args:
            task: 任务描述

        Returns:
            最终优化后的结果
        """
        print(f"\n{'='*70}")
        print("🚀 Reflection Agent - 自我反思优化")
        print(f"{'='*70}")
        print(f"任务: {task}")
        print(f"最大迭代次数: {self.max_iter}")
        print()

        # ========== Phase 1: 初始执行 ==========
        print(f"{'─'*70}")
        print("📝 Phase 1: 初始生成")
        print(f"{'─'*70}\n")

        initial_prompt = INITIAL_PROMPT.format(task=task)
        content = self._get_response(initial_prompt)
        self.memory.add_record("execution", content)

        print(f"\n✅ 第 1 版完成（{len(content)} 字符）")

        # ========== Phase 2: 迭代优化 ==========
        for i in range(self.max_iter):
            print(f"\n{'─'*70}")
            print(f"🔍 Phase 2.{i+1}: 反思审查")
            print(f"{'─'*70}\n")

            # 反思
            reflect_prompt = REFLECT_PROMPT.format(
                task=task,
                content=self.memory.get_last_execution()
            )
            feedback = self._get_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # 检查是否收敛
            if self._is_converged(feedback):
                print(f"\n🎯 已收敛，无需进一步优化")
                break

            print(f"\n⚠️ 发现可改进点，继续优化...")

            # 优化
            print(f"\n{'─'*70}")
            print(f"✨ Phase 2.{i+1}: 优化改进")
            print(f"{'─'*70}\n")

            refine_prompt = REFINE_PROMPT.format(
                task=task,
                last_content=self.memory.get_last_execution(),
                feedback=feedback
            )
            content = self._get_response(refine_prompt)
            self.memory.add_record("execution", content)

            print(f"\n✅ 第 {i+2} 版完成（{len(content)} 字符）")

        # ========== Phase 3: 输出结果 ==========
        print(f"\n{'='*70}")
        print("🎉 优化完成")
        print(f"{'='*70}")
        print(f"总迭代次数: {self.memory.get_iteration_count()}")
        print(f"反思次数: {len([r for r in self.memory.records if r['type'] == 'reflection'])}")
        print()

        # 显示完整历史
        print("📜 优化轨迹:")
        print(self.memory.get_trajectory())
        print()

        return self.memory.get_last_execution()


# ============ 5. 测试示例 ============

def main():
    """主函数 - 演示 Reflection Agent"""

    print("🚀 Reflection Agent 演示")
    print("=" * 70)
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
        agent = ReflectionAgent(llm, max_iterations=2)

        # 测试示例
        examples = [
            "写一个 Python 函数，计算斐波那契数列的第 n 项",
            "写一篇 200 字的自我介绍",
            "写一首关于春天的五言绝句",
            "解释什么是机器学习，用通俗的语言",
        ]

        print("📚 示例任务:")
        for i, ex in enumerate(examples, 1):
            print(f"   {i}. {ex}")
        print()

        # 交互式运行
        while True:
            try:
                task = input("\n📝 请输入任务 (quit 退出): ").strip()
                if task.lower() in ('quit', 'exit', 'q'):
                    break
                if not task:
                    continue

                agent.run(task)

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")


if __name__ == "__main__":
    main()
