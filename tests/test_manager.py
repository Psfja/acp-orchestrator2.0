import pytest
from src.agents.manager import AgentManager
from src.agents.adapter import ACPAdapter
from src.config.loader import AgentConfig


class FakeAdapter(ACPAdapter):
    def __init__(self):
        self.launched = False
        self.initialized = False
        self.prompts = []
        self.closed_sessions = []

    def get_launch_command(self) -> list[str]:
        return ["fake"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, config):
        self.initialized = True
        return f"sid-{id(self)}"

    async def send_prompt(self, writer, sid, prompt):
        self.prompts.append(prompt)

    async def read_updates(self, reader):
        yield {"type": "message", "content": "working..."}
        yield {"type": "message", "content": "done"}

    async def close_session(self, writer, sid):
        self.closed_sessions.append(sid)


@pytest.fixture
def manager():
    return AgentManager()


@pytest.fixture
def agent_config():
    return AgentConfig(
        name="测试Agent",
        command="fake",
        adapter="fake",
        role="executor",
        system_prompt="你是测试Agent",
    )


@pytest.mark.asyncio
async def test_register_adapter(manager):
    manager.register_adapter("fake", FakeAdapter)
    assert "fake" in manager._adapters


@pytest.mark.asyncio
async def test_spawn_agent(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)
    assert session.agent_key == "test-1"
    assert session.state == "active"


@pytest.mark.asyncio
async def test_send_task(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)

    updates = []
    async for update in manager.send_task(session, "编写一个函数"):
        updates.append(update)

    assert len(updates) == 2
    assert updates[0]["content"] == "working..."
    assert updates[1]["content"] == "done"


@pytest.mark.asyncio
async def test_kill_agent(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)
    await manager.kill(session)
    assert len(session.adapter.closed_sessions) == 1
