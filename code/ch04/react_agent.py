"""
ReAct Agent 实现
Reasoning + Acting 范式
"""

import os
import re
from typing import List, Dict


# ============ 1. LLM Client 封装 ============

class MockLLM:
    """模拟 LLM，用于演示 ReAct 流程"""

    def __init__(self):
        self.responses = []
        self.step = 0

    def set_scenario(self, question: str):
        """设置模拟场景"""
        if "25 * 4 + 100" in question or "计算" in question:
            self.responses = [
                # Step 1: Thought + Action
                "Thought: 我需要计算 25 * 4 + 100。根据运算优先级，先算乘法 25 * 4，再加 100。\n"
                "Action: Calculator[25 * 4]",
                # Step 2: Thought + Action
                "Thought: 已经得到 25 * 4 = 100。现在需要计算 100 + 100。\n"
                "Action: Calculator[100 + 100]",
                # Step 3: Finish
                "Thought: 已经得到 100 + 100 = 200。所以最终答案是 200。\n"
                "Action: Finish[200]",
            ]
        elif "天气" in question:
            self.responses = [
                "Thought: 用户询问北京今天的天气，我需要使用天气查询工具。\n"
                "Action: Weather[北京]",
                "Thought: 已经获取到北京天气信息，晴，25度。可以给出答案了。\n"
                "Action: Finish[北京今天天气晴朗，气温25摄氏度，适宜出行。]",
            ]
        else:
            self.responses = [
                "Thought: 这是一个直接回答的问题，不需要使用工具。\n"
                "Action: Finish[我是ReAct Agent，可以帮你计算和查询天气。]",
            ]

    def think(self, messages: List[Dict[str, str]], temperature=0) -> str:
        """模拟 LLM 调用"""
        print(f"🧠 调用 LLM...")
        if self.step < len(self.responses):
            response = self.responses[self.step]
            self.step += 1
            print(response)
            return response
        return "Action: Finish[任务完成]"


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
    """天气查询工具 - 模拟"""
    print(f"🔧 查询天气: {city}")
    # 模拟天气数据
    weather_db = {
        "北京": "晴，25°C",
        "上海": "多云，22°C",
        "广州": "小雨，28°C",
        "深圳": "阴，26°C",
    }
    return weather_db.get(city, f"暂无 {city} 的天气信息")


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
        print(f"✅ 注册工具: {name}")

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

可用工具：
{tools}

必须严格按以下格式回复：
Thought: 你的思考过程，分析问题并决定下一步
Action: 选择以下之一：
- ToolName[tool_input] : 调用工具（工具名[input]）
- Finish[final_answer] : 当你有最终答案时

问题: {question}
历史记录:
{history}
"""


class ReActAgent:
    """ReAct Agent 实现"""

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
        print(f"\n{'='*50}")
        print(f"🎯 问题: {question}")
        print(f"{'='*50}\n")

        self.history = []

        for step in range(1, self.max_steps + 1):
            print(f"\n--- 步骤 {step} ---")

            # 构建 Prompt
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=self.tools.get_tool_descriptions(),
                question=question,
                history="\n".join(self.history) if self.history else "（无）"
            )

            # 调用 LLM
            response = self.llm.think([{"role": "user", "content": prompt}])
            thought, action = self._parse_output(response)

            # 显示思考过程
            if thought:
                print(f"🤔 Thought: {thought}")

            if not action:
                print("❌ 未解析到 Action，结束")
                break

            # 检查是否结束
            if action.startswith("Finish"):
                match = re.match(r"Finish\[(.*)\]", action, re.DOTALL)
                if match:
                    answer = match.group(1)
                    print(f"\n🎉 最终答案: {answer}")
                    return answer
                else:
                    print("\n🎉 任务完成")
                    return "完成"

            # 执行工具
            tool_name, tool_input = self._parse_action(action)
            print(f"🎬 Action: {tool_name}[{tool_input}]")

            tool_func = self.tools.get_tool(tool_name)
            if tool_func:
                observation = tool_func(tool_input)
            else:
                observation = f"错误：工具 '{tool_name}' 不存在"

            print(f"👀 Observation: {observation}")

            # 记录历史
            self.history.extend([
                f"Thought: {thought}",
                f"Action: {action}",
                f"Observation: {observation}"
            ])

        print("\n⏹️ 达到最大步数限制")
        return None


# ============ 5. 运行示例 ============

def main():
    """主函数 - 演示 ReAct Agent"""

    print("🚀 ReAct Agent 演示")
    print("=" * 50)

    # 1. 创建工具执行器并注册工具
    tools = ToolExecutor()
    tools.register("Calculator", "计算器，用于数学运算，如 Calculator[25 * 4]", calculator)
    tools.register("Weather", "天气查询，如 Weather[北京]", weather_query)

    # 2. 创建模拟 LLM
    llm = MockLLM()

    # 3. 创建 Agent
    agent = ReActAgent(llm, tools, max_steps=5)

    # 4. 运行示例
    examples = [
        "计算 25 * 4 + 100 等于多少？",
        "北京今天天气怎么样？",
        "你能做什么？",
    ]

    for question in examples:
        llm.set_scenario(question)  # 设置模拟场景
        llm.step = 0  # 重置步骤计数
        agent.run(question)
        print("\n" + "=" * 50)

    print("\n✨ 演示结束！")
    print("\n说明：")
    print("- 这里使用 MockLLM 模拟 LLM 响应")
    print("- 实际使用时，替换为真实的 LLM Client")
    print("- ReAct 的核心是 Thought -> Action -> Observation 循环")


if __name__ == "__main__":
    main()
