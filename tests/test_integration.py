"""端到端集成测试 — 使用 MockAdapter 自动角色检测。"""
import io
import pytest
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.agents.adapters.mock import MockAdapter
from src.config.loader import AgentConfig, Settings, OrchestratorConfig
from src.logger.logger import Logger


def make_e2e_config():
    return OrchestratorConfig(
        settings=Settings(max_iterations=3),
        agents={
            "orchestrator": AgentConfig(
                name="编排Agent", command="mock", adapter="mock",
                role="orchestrator",
                system_prompt="编排拆分任务输出JSON",
            ),
            "backend-dev": AgentConfig(
                name="后端开发", command="mock", adapter="mock",
                role="executor",
                system_prompt="执行后端任务",
            ),
            "frontend-dev": AgentConfig(
                name="前端开发", command="mock", adapter="mock",
                role="executor",
                system_prompt="执行前端任务",
            ),
            "checker": AgentConfig(
                name="检查Agent", command="mock", adapter="mock",
                role="checker",
                system_prompt="检查审核代码",
            ),
            "tester": AgentConfig(
                name="测试Agent", command="mock", adapter="mock",
                role="tester",
                system_prompt="测试代码",
            ),
        },
    )


@pytest.mark.asyncio
async def test_full_happy_path():
    buf = io.StringIO()
    logger = Logger(output=buf)
    config = make_e2e_config()
    manager = AgentManager(logger=logger)
    manager.register_adapter("mock", MockAdapter)

    fsm = OrchestrationFSM(config=config, manager=manager, logger=logger)
    result = await fsm.run("开发一个登录页面")

    assert result["status"] == "completed"
    assert result["total_tasks"] == 3

    output = buf.getvalue()
    assert "idle" in output
    assert "orchestrating" in output
    assert "dispatching" in output
    assert "executing" in output
    assert "reviewing" in output
    assert "testing" in output
    assert "completed" in output
    assert "项目完成" in output
