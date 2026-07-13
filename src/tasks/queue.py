import asyncio
from src.tasks.models import Task, TaskStatus


class TaskQueue:

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    def enqueue(self, tasks: list[Task]) -> None:
        for task in tasks:
            self._tasks[task.id] = task

    def get_ready(self) -> list[Task]:
        done_ids = [tid for tid, t in self._tasks.items() if t.status == TaskStatus.DONE]
        ready = []
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING and task.is_ready(done_ids):
                ready.append(task)
        return ready

    async def mark_running(self, task_id: str) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].mark_running()

    async def mark_done(self, task_id: str, result: str) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].mark_done(result)

    async def mark_failed(self, task_id: str, error: str) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].mark_failed(error)

    def all_done(self) -> bool:
        if not self._tasks:
            return False
        return all(t.status == TaskStatus.DONE for t in self._tasks.values())

    def has_failed(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())

    def get_done_tasks(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.DONE]

    def get_failed_tasks(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.FAILED]

    def status_summary(self) -> str:
        total = len(self._tasks)
        done = len(self.get_done_tasks())
        bar_width = 10
        filled = int(bar_width * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"[{bar}] {done}/{total}"

    def clear(self) -> None:
        self._tasks.clear()
