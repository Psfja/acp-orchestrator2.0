"""验证 OpenHands 插件的创建和基本行为。"""
import pytest
from src.openhands.plugin import create_agent, ACPOrchestratorAgent


def test_create_agent():
    agent = create_agent()
    assert agent is not None
    assert isinstance(agent, ACPOrchestratorAgent)
    assert agent.config is not None
    assert agent.manager is not None


def test_agent_has_adapters():
    agent = create_agent()
    # 验证关键适配器已注册
    assert "claude_code" in agent.manager._adapters
    assert "codex" in agent.manager._adapters
    assert "gemini" in agent.manager._adapters
    assert "mock" in agent.manager._adapters


def test_agent_config_loaded():
    agent = create_agent()
    assert agent.config.settings.max_iterations == 5
    assert "orchestrator" in agent.config.agents


@pytest.mark.asyncio
async def test_agent_run_basic():
    agent = create_agent()
    result = await agent.run("测试: 写一个hello world")
    assert "status" in result
    assert result["status"] in ("completed", "failed")
