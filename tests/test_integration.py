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
                name="编排Agent",
                command="mock",
                adapter="mock",
                role="orchestrator",
                system_prompt="拆分任务，输出JSON",
            ),
            "worker": AgentConfig(
                name="执行Agent",
                command="mock",
                adapter="mock",
                role="executor",
                system_prompt="执行任务",
            ),
            "checker": AgentConfig(
                name="检查Agent",
                command="mock",
                adapter="mock",
                role="checker",
                system_prompt="检查代码",
            ),
            "tester": AgentConfig(
                name="测试Agent",
                command="mock",
                adapter="mock",
                role="tester",
                system_prompt="测试代码",
            ),
        },
    )


class OrchestratorMock(MockAdapter):
    def __init__(self):
        super().__init__(responses=[
            '好的，我拆分为以下任务:\n```json\n[{"id":"task_1","description":"编写登录页面","assigned_agent":"worker"},{"id":"task_2","description":"编写API","assigned_agent":"worker"}]\n```'
        ])


class WorkerMock(MockAdapter):
    def __init__(self):
        super().__init__(responses=["工作中...", "任务完成，已创建文件"])


class CheckerPassMock(MockAdapter):
    def __init__(self):
        super().__init__(responses=["所有任务审核通过，代码质量良好"])


class TesterPassMock(MockAdapter):
    def __init__(self):
        super().__init__(responses=["测试全部通过 3/3"])


@pytest.mark.asyncio
async def test_full_happy_path():
    buf = io.StringIO()
    logger = Logger(output=buf)
    config = make_e2e_config()
    manager = AgentManager(logger=logger)

    manager.register_adapter("mock", WorkerMock)

    fsm = OrchestrationFSM(config=config, manager=manager, logger=logger)

    orig_spawn = manager.spawn

    async def spawn_with_mock(agent_key, agent_config):
        if agent_key == "orchestrator":
            manager.register_adapter("mock", OrchestratorMock)
        elif agent_key.startswith("exec-"):
            manager.register_adapter("mock", WorkerMock)
        elif agent_key == "checker":
            manager.register_adapter("mock", CheckerPassMock)
        elif agent_key == "tester":
            manager.register_adapter("mock", TesterPassMock)
        return await orig_spawn(agent_key, agent_config)

    manager.spawn = spawn_with_mock

    result = await fsm.run("开发一个登录页面")

    assert result["status"] == "completed"
    assert result["total_tasks"] == 2

    output = buf.getvalue()
    assert "idle" in output
    assert "orchestrating" in output
    assert "dispatching" in output
    assert "executing" in output
    assert "reviewing" in output
    assert "testing" in output
    assert "completed" in output
    assert "项目完成" in output
