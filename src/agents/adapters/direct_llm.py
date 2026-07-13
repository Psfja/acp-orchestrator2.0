"""Direct LLM Adapter — 直接调 LLM API，绕过 ACP Agent。用于编排角色。"""

import os
import json
from openai import AsyncOpenAI
from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


class DirectLLMAdapter(ACPAdapter):
    """
    不启动子进程，直接调用 LLM API（兼容 OpenAI / DeepSeek 等）。
    用于编排 Agent —— 快速、确定性的 JSON 输出，无工具、无探索。
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        )
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        self._system_prompt = ""
        self._prompt_sent = ""

    def get_launch_command(self) -> list[str]:
        return ["direct-llm"]

    async def spawn(self):
        return None, None

    async def initialize(self, writer, reader, session_config: dict) -> str:
        self._system_prompt = session_config.get("systemPrompt", "")
        return "llm-session-001"

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        self._prompt_sent = prompt

    async def read_updates(self, reader) -> AsyncIterator[dict]:
        """调 LLM API，流式返回结果。"""
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": self._prompt_sent},
            ],
            stream=True,
        )

        full_text = ""
        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                full_text += delta.content
                yield {"type": "message", "content": delta.content}

        yield {"type": "message", "content": "\n"}

    async def close_session(self, writer, session_id: str) -> None:
        pass
