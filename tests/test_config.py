import os

import pytest

from src.config.loader import load_config, AgentConfig, Settings


def test_load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "agents.yaml")
    config = load_config(config_path)

    assert config.settings.max_iterations == 5
    assert config.settings.task_timeout_seconds == 300

    assert "orchestrator" in config.agents
    orch = config.agents["orchestrator"]
    assert orch.name == "编排Agent"
    assert orch.role == "orchestrator"

    assert "frontend-dev" in config.agents
    fe = config.agents["frontend-dev"]
    assert fe.role == "executor"

    assert "checker" in config.agents
    assert "tester" in config.agents


def test_get_agents_by_role():
    config_path = os.path.join(os.path.dirname(__file__), "..", "agents.yaml")
    config = load_config(config_path)

    executors = [a for a in config.agents.values() if a.role == "executor"]
    assert len(executors) >= 2


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")
