"""OpenHands 插件入口 — 将 ACP Orchestrator 嵌入为 OpenHands 自定义 Agent。"""

import os
from src.config.loader import load_config
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.logger.logger import Logger

# 导入所有适配器
from src.agents.adapters.claude_code import ClaudeCodeAdapter
from src.agents.adapters.codex import CodexAdapter
from src.agents.adapters.gemini import GeminiAdapter
from src.agents.adapters.copilot import CopilotAdapter
from src.agents.adapters.goose import GooseAdapter
from src.agents.adapters.cline import ClineAdapter
from src.agents.adapters.auggie import AuggieAdapter
from src.agents.adapters.kiro import KiroAdapter
from src.agents.adapters.opencode import OpenCodeAdapter
from src.agents.adapters.qwen_code import QwenCodeAdapter
from src.agents.adapters.vibe import VibeAdapter
from src.agents.adapters.droid import DroidAdapter
from src.agents.adapters.qoder import QoderAdapter
from src.agents.adapters.hermes import HermesAdapter
from src.agents.adapters.pi import PiAdapter
from src.agents.adapters.reasonix import ReasonixAdapter
from src.agents.adapters.openhands import OpenHandsAdapter
from src.agents.adapters.mock import MockAdapter


class ACPOrchestratorAgent:
    """OpenHands 兼容的编排 Agent 包装器。"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "agents.yaml")

        self.config_path = config_path
        self.config = load_config(config_path)
        self.logger = Logger()
        self.manager = self._setup_manager()

    def _setup_manager(self) -> AgentManager:
        manager = AgentManager(logger=self.logger)
        manager.register_adapter("mock", MockAdapter)
        manager.register_adapter("echo", MockAdapter)
        manager.register_adapter("claude_code", ClaudeCodeAdapter)
        manager.register_adapter("codex", CodexAdapter)
        manager.register_adapter("gemini", GeminiAdapter)
        manager.register_adapter("copilot", CopilotAdapter)
        manager.register_adapter("goose", GooseAdapter)
        manager.register_adapter("cline", ClineAdapter)
        manager.register_adapter("auggie", AuggieAdapter)
        manager.register_adapter("kiro", KiroAdapter)
        manager.register_adapter("opencode", OpenCodeAdapter)
        manager.register_adapter("qwen_code", QwenCodeAdapter)
        manager.register_adapter("vibe", VibeAdapter)
        manager.register_adapter("droid", DroidAdapter)
        manager.register_adapter("qoder", QoderAdapter)
        manager.register_adapter("hermes", HermesAdapter)
        manager.register_adapter("pi", PiAdapter)
        manager.register_adapter("reasonix", ReasonixAdapter)
        manager.register_adapter("openhands", OpenHandsAdapter)
        return manager

    async def run(self, requirement: str) -> dict:
        fsm = OrchestrationFSM(config=self.config, manager=self.manager, logger=self.logger)
        return await fsm.run(requirement)


def create_agent(config_path: str | None = None) -> ACPOrchestratorAgent:
    """OpenHands 插件工厂函数。"""
    return ACPOrchestratorAgent(config_path)
