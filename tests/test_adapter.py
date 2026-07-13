import asyncio
import pytest
from src.agents.adapter import ACPAdapter
from src.agents.session import AgentSession


class FakeAdapter(ACPAdapter):

    def __init__(self):
        self.launched = False
        self.initialized = False
        self.prompts_sent = []
        self.closed = False

    def get_launch_command(self) -> list[str]:
        return ["echo", "fake"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, session_config: dict) -> str:
        self.initialized = True
        self.system_prompt = session_config.get("systemPrompt", "")
        return "fake-session-001"

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        self.prompts_sent.append(prompt)

    async def read_updates(self, reader):
        yield {"type": "message", "content": "fake update"}

    async def close_session(self, writer, session_id: str) -> None:
        self.closed = True


def test_adapter_launch_command():
    adapter = FakeAdapter()
    assert adapter.get_launch_command() == ["echo", "fake"]


@pytest.mark.asyncio
async def test_adapter_lifecycle():
    adapter = FakeAdapter()
    writer, reader = await adapter.spawn()
    assert adapter.launched

    sid = await adapter.initialize(writer, reader, {"systemPrompt": "test prompt"})
    assert adapter.initialized
    assert adapter.system_prompt == "test prompt"
    assert sid == "fake-session-001"

    await adapter.send_prompt(writer, sid, "hello world")
    assert adapter.prompts_sent == ["hello world"]

    updates = [u async for u in adapter.read_updates(reader)]
    assert len(updates) == 1
    assert updates[0]["content"] == "fake update"

    await adapter.close_session(writer, sid)
    assert adapter.closed


def test_session_creation():
    from src.config.loader import AgentConfig
    config = AgentConfig(
        name="测试Agent",
        command="echo",
        adapter="fake",
        role="executor",
        system_prompt="test",
    )
    session = AgentSession(
        agent_key="test-agent",
        config=config,
    )
    assert session.agent_key == "test-agent"
    assert session.config.name == "测试Agent"
    assert session.state == "idle"
