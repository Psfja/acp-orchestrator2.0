from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    deps: list[str] = field(default_factory=list)

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_done(self, result: str) -> None:
        self.status = TaskStatus.DONE
        self.result = result
        self.error = None

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error

    def is_ready(self, done_task_ids: list[str]) -> bool:
        return all(dep in done_task_ids for dep in self.deps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "deps": self.deps,
        }
