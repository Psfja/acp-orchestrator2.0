from dataclasses import dataclass, field

import yaml


@dataclass
class Settings:
    max_iterations: int = 5
    task_timeout_seconds: int = 300
    global_timeout_seconds: int = 3600


@dataclass
class AgentConfig:
    name: str
    command: str
    adapter: str
    role: str  # orchestrator | executor | checker | tester
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
        agents[key] = AgentConfig(
            name=data["name"],
            command=data["command"],
            adapter=data["adapter"],
            role=data["role"],
            system_prompt=data.get("system_prompt", ""),
            config=data.get("config", {}),
        )

    return OrchestratorConfig(settings=settings, agents=agents)
