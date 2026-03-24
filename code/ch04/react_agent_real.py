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

        # 从当前目录加载 .env
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


# ============ 2.1 新增自定义工具 ============

def current_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间
    用法: CurrentTime[%Y-%m-%d %H:%M:%S] 或 CurrentTime[now]
    """
    from datetime import datetime
    print(f"🔧 获取当前时间")
    try:
        if format.lower() in ('now', 'today', 'current'):
            format = "%Y-%m-%d %H:%M:%S"
        return datetime.now().strftime(format)
    except Exception as e:
        return f"时间格式错误: {e}，使用默认格式: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def file_reader(filepath: str) -> str:
    """读取文件内容
    用法: FileReader[文件路径]
    注意: 只能读取项目目录下的文件，且有大小限制
    """
    import os
    print(f"🔧 读取文件: {filepath}")

    # 安全检查：禁止访问系统敏感文件
    forbidden = ['/etc/', '/sys/', '/proc/', '/dev/', 'C:\\Windows', '.ssh', '.env']
    for f in forbidden:
        if f in filepath:
            return f"错误：禁止访问敏感路径 {f}"

    # 限制在项目目录内
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(filepath):
        filepath = os.path.join(base_dir, filepath)

    try:
        if not os.path.exists(filepath):
            return f"错误：文件不存在 {filepath}"

        # 文件大小限制 100KB
        size = os.path.getsize(filepath)
        if size > 100 * 1024:
            return f"错误：文件过大 ({size} 字节)，限制 100KB"

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 截断过长内容
        if len(content) > 2000:
            content = content[:2000] + f"\n... (已截断，共 {len(content)} 字符)"

        return f"文件内容:\n{content}"

    except Exception as e:
        return f"读取错误: {e}"


def web_search(query: str) -> str:
    """模拟网页搜索
    用法: WebSearch[搜索关键词]
    注意: 这是模拟数据，实际使用时可以接入真实搜索API
    """
    print(f"🔧 搜索: {query}")

    # 模拟搜索结果数据库
    search_db = {
        "python": "Python 是一种流行的编程语言，由 Guido van Rossum 于 1991 年创建。特点：简洁易读、丰富的库、广泛应用。",
        "react": "React 是 Meta 开发的前端框架，使用组件化开发和虚拟 DOM。",
        "人工智能": "人工智能(AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
        "机器学习": "机器学习是 AI 的子集，通过数据训练模型，使计算机能够从经验中学习。",
        "docker": "Docker 是一个开源平台，用于开发、部署和运行应用程序的容器。",
        "git": "Git 是一个分布式版本控制系统，用于跟踪代码变更。",
    }

    # 简单匹配
    query_lower = query.lower()
    for keyword, result in search_db.items():
        if keyword in query_lower:
            return f"搜索结果: {result}"

    # 默认回复
    return f"搜索 '{query}' 没有找到精确结果。建议尝试: Python, React, 人工智能, 机器学习, Docker, Git"


def python_runner(code: str) -> str:
    """安全执行 Python 代码（受限环境）
    用法: PythonRunner[print('hello')]
    注意: 仅支持基础操作，禁止危险函数
    """
    import io
    import sys
    import math
    import random
    import json

    print(f"🔧 执行 Python 代码: {code[:50]}{'...' if len(code) > 50 else ''}")

    # 危险关键字检查
    dangerous = ['import os', 'import sys', 'exec(', 'eval(', '__import__',
                 'open(', 'file(', 'subprocess', 'shell', 'system(']
    for d in dangerous:
        if d in code.lower():
            return f"错误：代码包含危险操作 '{d}'，已禁止执行"

    # 创建受限执行环境
    safe_globals = {
        '__builtins__': {
            'print': print,
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'type': type,
            'isinstance': isinstance,
            'True': True,
            'False': False,
            'None': None,
        },
        'math': math,
        'random': random,
        'json': json,
    }

    # 捕获输出
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # 限制代码长度
        if len(code) > 1000:
            return "错误：代码过长，限制 1000 字符"

        exec(code, safe_globals, {})
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        return f"执行结果:\n{output}" if output else "执行成功（无输出）"

    except Exception as e:
        sys.stdout = old_stdout
        return f"执行错误: {e}"


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

    # 从当前目录加载 .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
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

        # 基础工具
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

        # 新增自定义工具
        tools.register(
            "CurrentTime",
            "获取当前时间，如 CurrentTime[now] 或 CurrentTime[%Y-%m-%d]",
            current_time
        )
        tools.register(
            "FileReader",
            "读取项目目录下的文件内容，如 FileReader[README.md]",
            file_reader
        )
        tools.register(
            "WebSearch",
            "网页搜索（模拟数据），如 WebSearch[Python教程]、WebSearch[Docker]",
            web_search
        )
        tools.register(
            "PythonRunner",
            "安全执行简单 Python 代码，如 PythonRunner[print(2+3)]、PythonRunner[import math; print(math.pi)]",
            python_runner
        )

        print(f"📦 已加载 {len(tools.tools)} 个工具:")
        for name in tools.tools.keys():
            print(f"   - {name}")
        print()

        # 3. 创建 Agent
        agent = ReActAgent(llm, tools, max_steps=5)

        # 4. 交互式运行
        print("💡 输入问题开始测试，输入 'quit' 退出")
        print("-" * 60)

        # 预设示例
        examples = [
            "计算 125 * 8 + 500 等于多少？",
            "北京和上海哪个城市今天更暖和？",
            "现在几点了？",
            "搜索一下 Python 是什么",
            "执行 Python 代码计算 100 的阶乘",
            "帮我读取 README.md 文件内容",
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
