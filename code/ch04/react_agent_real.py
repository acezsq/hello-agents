"""
ReAct Agent - 真实 LLM 版本
需要配置 .env 文件
"""

import os
import re
from typing import List, Dict
from dotenv import load_dotenv

# 尝试导入 openai，如果没有则给出提示
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  未安装 openai，请先运行: pip install openai python-dotenv")


# ============ 1. 真实 LLM Client ============

class HelloAgentsLLM:
    """真实 LLM 客户端 - 支持 OpenAI 格式 API"""

    def __init__(self, model=None, api_key=None, base_url=None, timeout=None):
        if not OPENAI_AVAILABLE:
            raise ImportError("请先安装 openai: pip install openai")

        load_dotenv()

        self.model = model or os.getenv("LLM_MODEL_ID", "gpt-3.5-turbo")
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))

        if not api_key:
            raise ValueError("未设置 LLM_API_KEY，请检查 .env 文件")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

    def think(self, messages: List[Dict[str, str]], temperature=0) -> str:
        """调用 LLM 获取响应"""
        print(f"🧠 调用模型: {self.model}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
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


# ============ 2. 工具定义 ============

def calculator(expression: str) -> str:
    """计算器工具 - 安全计算数学表达式"""
    print(f"🔧 执行计算器: {expression}")
    try:
        # 只允许数字和基本运算符
        allowed = set('0123456789+-*/.() ')
        if not all(c in allowed for c in expression):
            return "错误：表达式包含非法字符"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def weather_query(city: str) -> str:
    """天气查询工具 - 模拟数据"""
    print(f"🔧 查询天气: {city}")
    weather_db = {
        "北京": "晴，25°C，空气质量良",
        "上海": "多云，22°C，微风",
        "广州": "小雨，28°C，湿度较高",
        "深圳": "阴，26°C，适宜出行",
        "杭州": "晴，24°C，西湖风景优美",
    }
    return weather_db.get(city, f"暂无 {city} 的天气信息，请尝试其他城市")


# ============ 3. 工具执行器 ============

class ToolExecutor:
    """工具执行器 - 管理和执行工具"""

    def __init__(self):
        self.tools = {}

    def register(self, name: str, description: str, func: callable):
        """注册工具"""
        self.tools[name] = {
            "description": description,
            "func": func
        }

    def get_tool(self, name: str) -> callable:
        """获取工具函数"""
        tool = self.tools.get(name)
        return tool["func"] if tool else None

    def get_tool_descriptions(self) -> str:
        """获取所有工具描述"""
        lines = []
        for name, info in self.tools.items():
            lines.append(f"- {name}: {info['description']}")
        return "\n".join(lines)


# ============ 4. ReAct Agent ============

REACT_PROMPT_TEMPLATE = """你是一个智能助手，可以使用外部工具解决问题。

## 可用工具

{tools}

## 回复格式

必须严格按以下格式回复：

Thought: 你的思考过程，分析问题并决定下一步
Action: 选择以下之一：
- 工具调用格式: 工具名[工具参数]
- 结束格式: Finish[最终答案]

## 示例

问题: 计算 2 + 3
Thought: 这是一个简单的加法计算，我需要使用计算器
Action: Calculator[2 + 3]

Observation: 5

Thought: 已经得到计算结果 5
Action: Finish[5]

## 当前任务

问题: {question}

## 历史记录

{history}

现在请回复：
"""


class ReActAgent:
    """ReAct Agent 实现 - 真实 LLM 版本"""

    def __init__(self, llm_client, tool_executor: ToolExecutor, max_steps=5):
        self.llm = llm_client
        self.tools = tool_executor
        self.max_steps = max_steps
        self.history = []

    def _parse_output(self, text: str) -> tuple:
        """解析 LLM 输出，提取 Thought 和 Action"""
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None

        return thought, action

    def _parse_action(self, action_text: str) -> tuple:
        """解析 Action，提取工具名和输入"""
        # 匹配 ToolName[input] 格式
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def run(self, question: str) -> str:
        """运行 ReAct Agent"""
        print(f"\n{'='*60}")
        print(f"🎯 问题: {question}")
        print(f"{'='*60}\n")

        self.history = []

        for step in range(1, self.max_steps + 1):
            print(f"\n{'─'*40}")
            print(f"📍 步骤 {step}/{self.max_steps}")
            print(f"{'─'*40}")

            # 构建 Prompt
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=self.tools.get_tool_descriptions(),
                question=question,
                history="\n".join(self.history) if self.history else "（无历史记录）"
            )

            # 调用 LLM
            try:
                response = self.llm.think([{"role": "user", "content": prompt}])
            except Exception as e:
                print(f"❌ LLM 调用失败: {e}")
                return None

            thought, action = self._parse_output(response)

            # 显示思考过程
            if thought:
                print(f"\n🤔 Thought:\n{thought}")

            if not action:
                print("❌ 未解析到 Action，结束")
                break

            # 检查是否结束
            if action.startswith("Finish"):
                match = re.match(r"Finish\[(.*)\]", action, re.DOTALL)
                if match:
                    answer = match.group(1)
                    print(f"\n{'='*60}")
                    print(f"🎉 最终答案: {answer}")
                    print(f"{'='*60}")
                    return answer
                else:
                    print("\n🎉 任务完成")
                    return "完成"

            # 执行工具
            tool_name, tool_input = self._parse_action(action)
            print(f"\n🎬 Action: {tool_name}[{tool_input}]")

            tool_func = self.tools.get_tool(tool_name)
            if tool_func:
                observation = tool_func(tool_input)
            else:
                observation = f"错误：工具 '{tool_name}' 不存在。可用工具: {list(self.tools.tools.keys())}"

            print(f"👀 Observation: {observation}")

            # 记录历史
            self.history.extend([
                f"Step {step}:",
                f"Thought: {thought}",
                f"Action: {action}",
                f"Observation: {observation}"
            ])

        print(f"\n{'='*60}")
        print("⏹️ 达到最大步数限制")
        print(f"{'='*60}")
        return None


# ============ 5. 使用示例 ============

def main():
    """主函数 - 演示真实 LLM 版本"""

    print("🚀 ReAct Agent - 真实 LLM 版本")
    print("=" * 60)
    print()

    # 检查环境变量
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL_ID")

    print("📋 环境检查:")
    print(f"   LLM_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"   LLM_MODEL_ID: {model or '❌ 未设置'}")
    print()

    if not api_key:
        print("⚠️  请先创建 .env 文件并配置 API 密钥:")
        print()
        print("   # .env 文件内容")
        print('   LLM_API_KEY="your-api-key"')
        print('   LLM_MODEL_ID="gpt-3.5-turbo"')
        print('   LLM_BASE_URL="https://api.openai.com/v1"  # 可选')
        print()
        print("   支持的模型服务商:")
        print("   - OpenAI: https://api.openai.com/v1")
        print("   - 阿里云百炼: https://dashscope.aliyuncs.com/compatible-mode/v1")
        print("   - 其他 OpenAI 格式 API")
        return

    try:
        # 1. 创建 LLM 客户端
        print("🔌 连接 LLM...")
        llm = HelloAgentsLLM()
        print(f"   模型: {llm.model}")
        print()

        # 2. 创建工具执行器并注册工具
        tools = ToolExecutor()
        tools.register(
            "Calculator",
            "计算器，用于数学运算，如 Calculator[25 * 4]、Calculator[100 + 200 - 50]",
            calculator
        )
        tools.register(
            "Weather",
            "天气查询，获取城市天气信息，如 Weather[北京]、Weather[上海]",
            weather_query
        )

        # 3. 创建 Agent
        agent = ReActAgent(llm, tools, max_steps=5)

        # 4. 交互式运行
        print("💡 输入问题开始测试，输入 'quit' 退出")
        print("-" * 60)

        # 预设示例
        examples = [
            "计算 125 * 8 + 500 等于多少？",
            "北京和上海哪个城市今天更暖和？",
        ]

        print("\n📚 示例问题（可直接复制使用）:")
        for i, ex in enumerate(examples, 1):
            print(f"   {i}. {ex}")
        print()

        while True:
            try:
                question = input("\n📝 请输入问题: ").strip()
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
        return


if __name__ == "__main__":
    main()
