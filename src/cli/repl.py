"""交互式 REPL — 类 Claude Code 的持续对话编排体验。"""

import asyncio
import os
import sys
import datetime
from src.config.loader import load_config
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.logger.logger import Logger
from src.cli.display import Display

from src.agents.adapters.mock import MockAdapter
from src.agents.adapters.claude_code import ClaudeCodeAdapter
from src.agents.adapters.codex import CodexAdapter
from src.agents.adapters.opencode import OpenCodeAdapter
from src.agents.adapters.reasonix import ReasonixAdapter
from src.agents.adapters.pi import PiAdapter


class OrchestratorREPL:
    """编排器交互式 REPL。"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "agents.yaml")

        self.config_path = config_path
        self.config = load_config(config_path)
        self.display = Display()
        self.session_history: list[dict] = []
        self.turn = 0

        self._setup_adapters()

    def _setup_adapters(self):
        # 已安装的 Agent → 真实适配器；未安装的 → MockAdapter 兜底
        self._adapter_registry = {
            "mock": MockAdapter,
            "echo": MockAdapter,
            "claude_code": ClaudeCodeAdapter,
            "codex": CodexAdapter,
            "opencode": OpenCodeAdapter,
            "reasonix": ReasonixAdapter,
            "pi": PiAdapter,
            # 未安装的 Agent 使用 MockAdapter
            "gemini": MockAdapter,
            "copilot": MockAdapter,
            "goose": MockAdapter,
            "cline": MockAdapter,
            "auggie": MockAdapter,
            "kiro": MockAdapter,
            "qwen_code": MockAdapter,
            "vibe": MockAdapter,
            "droid": MockAdapter,
            "qoder": MockAdapter,
            "hermes": MockAdapter,
            "openhands": MockAdapter,
        }

    def _make_manager(self) -> AgentManager:
        manager = AgentManager()
        for name, cls in self._adapter_registry.items():
            manager.register_adapter(name, cls)
        return manager

    async def run_requirement(self, requirement: str) -> dict:
        """运行一次编排流程。"""
        self.turn += 1
        manager = self._make_manager()

        # 使用带时间戳的日志输出
        fsm = OrchestrationFSM(config=self.config, manager=manager, logger=Logger())

        self.display.section(f"第 {self.turn} 轮编排")
        self.display.system_info(f"需求: {requirement[:100]}...")
        start = datetime.datetime.now()

        result = await fsm.run(requirement)

        elapsed = (datetime.datetime.now() - start).total_seconds()
        result["elapsed"] = f"{elapsed:.1f}秒"
        result["requirement"] = requirement
        result["turn"] = self.turn

        self.session_history.append(result)
        return result

    async def start(self) -> None:
        """启动 REPL 主循环。"""
        self.display.banner()

        while True:
            try:
                user_input = self.display.prompt()

                if not user_input or not user_input.strip():
                    continue

                cmd = user_input.strip()

                # 处理命令
                if cmd.startswith("/"):
                    if await self._handle_command(cmd):
                        continue
                    else:
                        break  # /exit

                # 正常运行编排
                result = await self.run_requirement(cmd)
                self.display.result_card(result)

                if result["status"] == "completed":
                    self.display.success(f"第 {self.turn} 轮完成")
                else:
                    self.display.error(f"第 {self.turn} 轮失败: {result.get('reason', '未知')}")

                self.display.separator()

            except KeyboardInterrupt:
                print()
                self.display.warn("当前操作已取消")
                continue
            except EOFError:
                print()
                break

        print()
        self.display.system_info(f"会话结束。共 {self.turn} 轮。再见。")

    async def _handle_command(self, cmd: str) -> bool:
        """处理 /help /status /clear /agents /exit 等命令。返回 True 继续，False 退出。"""
        parts = cmd.split()
        action = parts[0].lower()

        if action == "/exit" or action == "/quit":
            return False

        elif action == "/help":
            self.display.show_help()

        elif action == "/status":
            self._show_status()

        elif action == "/clear":
            self.session_history.clear()
            self.turn = 0
            self.display.success("上下文已清除")

        elif action == "/agents":
            self.display.show_agents(self.config.agents)

        else:
            self.display.warn(f"未知命令: {action}，输入 /help 查看帮助")

        return True

    def _show_status(self) -> None:
        print()
        print(f"  会话轮次: {self.turn}")
        print(f"  已完成: {len([r for r in self.session_history if r['status'] == 'completed'])}")
        print(f"  失败: {len([r for r in self.session_history if r['status'] == 'failed'])}")
        print(f"  配置: {self.config_path}")
        print(f"  Agent数: {len(self.config.agents)}")
        print()


def main():
    repl = OrchestratorREPL()
    asyncio.run(repl.start())


if __name__ == "__main__":
    main()
