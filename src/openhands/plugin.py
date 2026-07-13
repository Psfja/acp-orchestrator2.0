"""OpenHands 插件入口 — 将 ACP Orchestrator 嵌入为 OpenHands 自定义 Agent。"""

from src.config.loader import load_config, get_default_config_path
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.logger.logger import Logger


class ACPOrchestratorAgent:
    """OpenHands 兼容的编排 Agent 包装器。"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = get_default_config_path()

        self.config_path = config_path
        self.config = load_config(config_path)
        self.logger = Logger()
        self.manager = self._setup_manager()

    def _setup_manager(self) -> AgentManager:
        from src.config.registry import register_all_adapters
        manager = AgentManager(logger=self.logger)
        register_all_adapters(manager)
        return manager

    async def run(self, requirement: str) -> dict:
        fsm = OrchestrationFSM(config=self.config, manager=self.manager, logger=self.logger)
        return await fsm.run(requirement)


def create_agent(config_path: str | None = None) -> ACPOrchestratorAgent:
    """OpenHands 插件工厂函数。"""
    return ACPOrchestratorAgent(config_path)
