from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


class MockAdapter(ACPAdapter):

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["任务完成"]
        self._idx = 0
        self.launched = False
        self.initialized = False
        self.prompts: list[str] = []
        self.closed = False
        self._system_prompt = ""

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
        for resp in self.responses:
            yield {"type": "message", "content": resp}
        self._idx = 0

    async def close_session(self, writer, session_id: str) -> None:
        self.closed = True
