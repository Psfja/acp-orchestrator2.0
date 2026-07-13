from dataclasses import dataclass
from src.config.loader import AgentConfig


@dataclass
class AgentSession:
    agent_key: str
    config: AgentConfig
    state: str = "idle"
    adapter: object = None
    writer: object = None
    reader: object = None
    session_id: str = ""

    def mark_active(self) -> None:
        self.state = "active"

    def mark_done(self) -> None:
        self.state = "done"

    def mark_error(self) -> None:
        self.state = "error"
