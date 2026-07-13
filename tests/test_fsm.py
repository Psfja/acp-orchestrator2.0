import io
import pytest
from src.fsm.states import OrchestrationState
from src.fsm.engine import OrchestrationFSM
from src.tasks.models import Task
from src.agents.manager import AgentManager
from src.agents.adapter import ACPAdapter
from src.config.loader import AgentConfig, Settings, OrchestratorConfig
from src.logger.logger import Logger


class EchoAdapter(ACPAdapter):

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["完成"]
        self._idx = 0
        self.launched = False
        self.initialized = False
        self.prompts = []
        self.closed = False

    def get_launch_command(self) -> list[str]:
        return ["echo"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, config):
        self.initialized = True
        return f"sid-{id(self)}"

    async def send_prompt(self, writer, sid, prompt):
        self.prompts.append(prompt)

    async def read_updates(self, reader):
        yield {"type": "message", "content": "工作中..."}
        yield {"type": "message", "content": self.responses[self._idx % len(self.responses)]}
        self._idx += 1

    async def close_session(self, writer, sid):
        self.closed = True


def make_test_config():
    return OrchestratorConfig(
        settings=Settings(max_iterations=3),
        agents={
            "orchestrator": AgentConfig(
                name="编排", adapter="echo",
                role="orchestrator",
                system_prompt="拆分任务，输出JSON",
            ),
            "worker": AgentConfig(
                name="执行", adapter="echo",
                role="executor",
                system_prompt="执行任务",
            ),
            "checker": AgentConfig(
                name="检查", adapter="echo",
                role="checker",
                system_prompt="检查代码",
            ),
            "tester": AgentConfig(
                name="测试", adapter="echo",
                role="tester",
                system_prompt="测试代码",
            ),
        },
    )


@pytest.fixture
def fsm():
    buf = io.StringIO()
    logger = Logger(output=buf)
    config = make_test_config()
    manager = AgentManager(logger=logger)
    engine = OrchestrationFSM(config=config, manager=manager, logger=logger)
    return engine


@pytest.mark.asyncio
async def test_fsm_initial_state(fsm):
    assert fsm.state == OrchestrationState.IDLE
    assert fsm.iteration == 0


@pytest.mark.asyncio
async def test_fsm_idle_to_orchestrating(fsm):
    fsm._transition(OrchestrationState.ORCHESTRATING)
    assert fsm.state == OrchestrationState.ORCHESTRATING


@pytest.mark.asyncio
async def test_fsm_invalid_transition(fsm):
    with pytest.raises(ValueError):
        fsm._transition(OrchestrationState.COMPLETED)


def test_fsm_parse_tasks_pure_json():
    fsm = OrchestrationFSM(config=make_test_config(), manager=AgentManager(), logger=Logger(output=io.StringIO()))
    json_str = '''
    [
        {"id": "task_1", "description": "前端页面", "assigned_agent": "worker"},
        {"id": "task_2", "description": "后端API", "assigned_agent": "worker"}
    ]
    '''
    tasks = fsm._parse_tasks(json_str)
    assert len(tasks) == 2
    assert tasks[0].id == "task_1"
    assert tasks[1].id == "task_2"


def test_fsm_parse_invalid_json():
    fsm = OrchestrationFSM(config=make_test_config(), manager=AgentManager(), logger=Logger(output=io.StringIO()))
    tasks = fsm._parse_tasks("这不是JSON")
    assert tasks == []


def test_fsm_parse_json_with_markdown_wrapper():
    fsm = OrchestrationFSM(config=make_test_config(), manager=AgentManager(), logger=Logger(output=io.StringIO()))
    text = '好的，我拆分为以下任务:\n```json\n[{"id":"t1","description":"测试","assigned_agent":"worker"}]\n```'
    tasks = fsm._parse_tasks(text)
    assert len(tasks) == 1
    assert tasks[0].id == "t1"
