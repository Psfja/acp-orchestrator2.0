"""终端显示 — 交互式 CLI 的格式化输出。"""

import shutil


class Display:
    """Rich 终端输出，带颜色和布局。"""

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self):
        self.width = shutil.get_terminal_size().columns

    def _print(self, text: str) -> None:
        print(text)

    def banner(self) -> None:
        print(self.CYAN + "=" * self.width + self.RESET)
        print(self.BOLD + self.CYAN + "  ACP Orchestrator — 多 Agent 编排框架" + self.RESET)
        print(self.GRAY + "  编排 Agent 拆分任务 → 执行 Agent 并行工作 → 检查 → 测试 → 交付" + self.RESET)
        print(self.GRAY + "  输入需求开始，输入 /help 查看命令，/exit 退出" + self.RESET)
        print(self.CYAN + "=" * self.width + self.RESET)
        print()

    def prompt(self) -> str:
        return input(self.BOLD + self.GREEN + "> " + self.RESET)

    def agent_message(self, agent: str, content: str) -> None:
        lines = content.strip().split("\n")
        prefix = self.YELLOW + f"[{agent}]" + self.RESET
        for line in lines:
            print(f"  {prefix} {line}")

    def system_info(self, msg: str) -> None:
        print(self.GRAY + f"  · {msg}" + self.RESET)

    def success(self, msg: str) -> None:
        print(self.GREEN + f"  OK {msg}" + self.RESET)

    def warn(self, msg: str) -> None:
        print(self.YELLOW + f"  ! {msg}" + self.RESET)

    def error(self, msg: str) -> None:
        print(self.RED + f"  X {msg}" + self.RESET)

    def separator(self) -> None:
        print(self.GRAY + "  " + "-" * min(self.width - 4, 60) + self.RESET)

    def section(self, title: str) -> None:
        print()
        print(self.BOLD + self.BLUE + f"  ◆ {title}" + self.RESET)

    def progress_bar(self, done: int, total: int, label: str = "") -> None:
        bar_w = 20
        filled = int(bar_w * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_w - filled)
        print(self.CYAN + f"  [{bar}] {done}/{total} {label}" + self.RESET)

    def result_card(self, result: dict) -> None:
        print()
        print(self.GREEN + "  ┌" + "─" * 40 + "┐" + self.RESET)
        print(self.GREEN + f"  │ 状态: {result['status']:<33}│" + self.RESET)
        print(self.GREEN + f"  │ 迭代: {result.get('iterations', '-'):<33}│" + self.RESET)
        print(self.GREEN + f"  │ 任务: {result.get('total_tasks', '-'):<33}│" + self.RESET)
        print(self.GREEN + f"  │ 耗时: {result.get('elapsed', '-'):<33}│" + self.RESET)
        print(self.GREEN + "  └" + "─" * 40 + "┘" + self.RESET)
        print()

    def show_help(self) -> None:
        print()
        print(self.BOLD + "  命令列表:" + self.RESET)
        print(f"  {self.CYAN}/help{self.RESET}    - 显示此帮助")
        print(f"  {self.CYAN}/status{self.RESET}  - 查看当前会话状态")
        print(f"  {self.CYAN}/clear{self.RESET}   - 清除对话上下文")
        print(f"  {self.CYAN}/agents{self.RESET}  - 列出可用 Agent")
        print(f"  {self.CYAN}/exit{self.RESET}    - 退出")
        print()
        print(f"  {self.GRAY}直接输入需求描述即可开始编排{self.RESET}")
        print()

    def show_agents(self, agents: dict) -> None:
        print()
        for key, agent in agents.items():
            role_icon = {"orchestrator": "🧠", "executor": "⚡", "checker": "🔍", "tester": "🧪"}.get(agent.role, "❓")
            print(f"  {role_icon} {self.BOLD}{key}{self.RESET} — {agent.name} ({self.GRAY}{agent.adapter}{self.RESET})")
        print()
