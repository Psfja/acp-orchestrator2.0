"""Mock ACP Adapter — 根据角色自动生成合适的模拟响应。"""

import json
from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


ORCHESTRATOR_RESPONSE = """好的，我分析后将需求拆分为以下任务:

```json
[
    {"id": "task_1", "description": "设计数据库schema：用户表、账单表、分类表", "assigned_agent": "backend-dev"},
    {"id": "task_2", "description": "编写后端API：CRUD账单、统计接口", "assigned_agent": "backend-dev"},
    {"id": "task_3", "description": "编写前端页面：记账入口、账单列表、统计图表", "assigned_agent": "frontend-dev"}
]
```
"""

EXECUTOR_RESPONSE = """工作中...
已完成任务，创建了以下文件:
- 相关代码文件已生成
- 功能实现完整，包含必要的错误处理
任务完成。"""

CHECKER_RESPONSE = """审核完成。
代码质量良好，所有功能按要求实现。
审核结果: 通过"""

TESTER_RESPONSE = """测试执行完成。
测试用例: 10个
通过: 10个
未通过: 0个
测试结果: 全部通过"""


class MockAdapter(ACPAdapter):
    """模拟 ACP Agent，根据 system_prompt 中的角色自动返回合适的响应。"""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses
        self._idx = 0
        self.launched = False
        self.initialized = False
        self.prompts: list[str] = []
        self.closed = False
        self._system_prompt = ""

    def _get_auto_responses(self) -> list[str]:
        sp = self._system_prompt
        if "编排" in sp or "拆分" in sp or "指派" in sp:
            return [ORCHESTRATOR_RESPONSE]
        elif "审查" in sp or "检查" in sp or "审核" in sp:
            return [CHECKER_RESPONSE]
        elif "测试" in sp:
            return [TESTER_RESPONSE]
        else:
            return [EXECUTOR_RESPONSE]

    def get_launch_command(self) -> list[str]:
        return ["mock"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, session_config: dict) -> str:
        self.initialized = True
        self._system_prompt = session_config.get("systemPrompt", "")
        return "mock-session-001"

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        self.prompts.append(prompt)

    async def read_updates(self, reader) -> AsyncIterator[dict]:
        responses = self.responses if self.responses else self._get_auto_responses()
        for resp in responses:
            yield {"type": "message", "content": resp}
        self._idx = 0

    async def close_session(self, writer, session_id: str) -> None:
        self.closed = True
