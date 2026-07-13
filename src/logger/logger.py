import sys
import datetime
from typing import TextIO


class Logger:

    def __init__(self, output: TextIO = sys.stdout):
        self.output = output

    def _write(self, tag: str, msg: str) -> None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.output.write(f"[{now}] [{tag}] {msg}\n")

    def _write_flush(self, tag: str, msg: str) -> None:
        self._write(tag, msg)
        self.output.flush()

    def log_state(self, from_state: str, to_state: str, iteration: int = 1) -> None:
        self._write_flush("状态", f"{from_state} → {to_state} (第{iteration}轮)")

    def log_orch(self, msg: str) -> None:
        self._write("编排→脚本", msg)

    def log_router(self, msg: str) -> None:
        self._write("脚本", msg)

    def log_exec(self, agent_name: str, msg: str) -> None:
        self._write(f"{agent_name}→脚本", msg)

    def log_check(self, msg: str) -> None:
        self._write("检查Agent→脚本", msg)

    def log_test(self, msg: str) -> None:
        self._write("测试Agent→脚本", msg)

    def log_error(self, msg: str) -> None:
        self._write_flush("错误", msg)

    def log_progress(self, done: int, total: int, iteration: int) -> None:
        bar_width = 10
        filled = int(bar_width * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        self._write("进度", f"轮次{iteration} [{bar}] {done}/{total}")

    def log_completed(self, total_iterations: int, total_tasks: int, elapsed: str) -> None:
        self._write_flush("系统", f"项目完成! 共{total_iterations}轮迭代, {total_tasks}个任务, 耗时{elapsed}")

    def log_failed(self, reason: str) -> None:
        self._write_flush("系统", f"流程失败: {reason}")
