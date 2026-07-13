import os
from dataclasses import dataclass, field
import yaml

VALID_ROLES = {"orchestrator", "executor", "checker", "tester"}


@dataclass
class Settings:
    max_iterations: int = 5
    task_timeout_seconds: int = 300


@dataclass
class AgentConfig:
    name: str
    adapter: str
    role: str
    system_prompt: str = ""
    config: dict = field(default_factory=dict)


@dataclass
class OrchestratorConfig:
    settings: Settings
    agents: dict[str, AgentConfig]


def load_config(path: str) -> OrchestratorConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    settings = Settings(**raw.get("settings", {}))

    agents = {}
    for key, data in raw.get("agents", {}).items():
        if "name" not in data:
            raise ValueError(f"Agent '{key}' 缺少必填字段: name")
        if "adapter" not in data:
            raise ValueError(f"Agent '{key}' 缺少必填字段: adapter")
        if "role" not in data:
            raise ValueError(f"Agent '{key}' 缺少必填字段: role")
        if data["role"] not in VALID_ROLES:
            raise ValueError(f"Agent '{key}' 的 role 无效: {data['role']}，有效值: {VALID_ROLES}")

        agents[key] = AgentConfig(
            name=data["name"],
            adapter=data["adapter"],
            role=data["role"],
            system_prompt=data.get("system_prompt", ""),
            config=data.get("config", {}),
        )

    if "orchestrator" not in agents:
        raise ValueError("agents.yaml 中缺少必填的 orchestrator Agent")

    return OrchestratorConfig(settings=settings, agents=agents)


def get_default_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "agents.yaml")
