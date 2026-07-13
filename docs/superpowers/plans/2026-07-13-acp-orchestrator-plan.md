# ACP Orchestrator 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 ACP 协议的多 Agent 编排框架，编排 Agent 拆分任务→执行 Agent 并行工作→检查 Agent 审核→测试 Agent 验证→不通过则返工循环。

**Architecture:** Python 3.11+ asyncio 应用。FSM 状态机控制全局流转，TaskQueue 管理任务分发，AgentManager 通过 ACP stdin/stdout 管理各 Agent 子进程。全部 4 个核心模块通过明确接口协作，Logger 实时输出所有通信。

**Tech Stack:** Python 3.11+, asyncio, PyYAML, agent-client-protocol (ACP SDK), pytest, pytest-asyncio

---

## 文件结构总览

```
acp-orchestrator/
├── agents.yaml
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py
│   ├── fsm/
│   │   ├── __init__.py
│   │   ├── states.py
│   │   ├── engine.py
│   │   └── context.py          # Phase 2
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── adapter.py
│   │   ├── session.py
│   │   └── adapters/
│   │       ├── __init__.py
│   │       └── mock.py         # Phase 1 (测试用)
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── queue.py
│   ├── logger/
│   │   ├── __init__.py
│   │   └── logger.py
│   └── openhands/              # Phase 4
│       ├── __init__.py
│       └── plugin.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_config.py
    ├── test_logger.py
    ├── test_adapter.py
    ├── test_manager.py
    ├── test_task_queue.py
    ├── test_fsm.py
    └── test_integration.py
```

---

## Phase 1: 核心骨架（MVP）

**目标:** 1个编排 Agent + 1个执行 Agent，打通线性流程（无返工循环）

### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `src/config/__init__.py`
- Create: `src/fsm/__init__.py`
- Create: `src/agents/__init__.py`
- Create: `src/agents/adapters/__init__.py`
- Create: `src/tasks/__init__.py`
- Create: `src/logger/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "acp-orchestrator"
version = "0.1.0"
description = "Multi-agent orchestration framework based on ACP protocol"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "agent-client-protocol>=0.11.0",
]
license = {text = "MIT"}

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-asyncio>=0.23",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: 创建所有 `__init__.py` 空文件**

Run:
```bash
cd "D:\acp agent" && mkdir -p src/config src/fsm src/agents/adapters src/tasks src/logger src/openhands tests
```

然后为每个目录创建空的 `__init__.py`。用 Write 工具创建 `src/__init__.py`、`src/config/__init__.py`、`src/fsm/__init__.py`、`src/agents/__init__.py`、`src/agents/adapters/__init__.py`、`src/tasks/__init__.py`、`src/logger/__init__.py`、`tests/__init__.py`，内容为空。

- [ ] **Step 3: 创建 tests/conftest.py**

```python
import asyncio
import pytest


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

- [ ] **Step 4: 安装依赖并验证**

Run: `pip install -e ".[dev]"`

Expected: 无错误，`pip list | grep acp-orchestrator` 显示 0.1.0

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold project structure with pyproject.toml"
```

---

### Task 2: 数据模型

**Files:**
- Create: `src/tasks/models.py`
- Create: `src/fsm/states.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 编写 tasks/models.py 测试**

创建 `tests/test_models.py`:

```python
import pytest
from src.tasks.models import Task, TaskStatus


def test_task_creation():
    task = Task(id="task_1", description="编写登录页面", assigned_agent="frontend-dev")
    assert task.id == "task_1"
    assert task.description == "编写登录页面"
    assert task.assigned_agent == "frontend-dev"
    assert task.status == TaskStatus.PENDING
    assert task.result is None
    assert task.error is None


def test_task_status_enum():
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.DONE.value == "done"
    assert TaskStatus.FAILED.value == "failed"


def test_task_mark_done():
    task = Task(id="task_1", description="test", assigned_agent="agent-a")
    task.mark_done("完成了 login.html")
    assert task.status == TaskStatus.DONE
    assert task.result == "完成了 login.html"


def test_task_mark_failed():
    task = Task(id="task_1", description="test", assigned_agent="agent-a")
    task.mark_failed("连接超时")
    assert task.status == TaskStatus.FAILED
    assert task.error == "连接超时"


def test_task_mark_running():
    task = Task(id="task_1", description="test", assigned_agent="agent-a")
    task.mark_running()
    assert task.status == TaskStatus.RUNNING


def test_task_to_dict():
    task = Task(id="task_1", description="编写登录页面", assigned_agent="frontend-dev")
    task.mark_done("完成")
    d = task.to_dict()
    assert d["id"] == "task_1"
    assert d["status"] == "done"
    assert d["result"] == "完成"


def test_task_dependencies():
    task = Task(id="task_2", description="test", assigned_agent="agent-a", deps=["task_1"])
    assert task.deps == ["task_1"]
    assert task.is_ready([]) is False
    assert task.is_ready(["task_1"]) is True
    assert task.is_ready(["task_0"]) is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_models.py -v`
Expected: 全部 FAIL (ImportError)

- [ ] **Step 3: 实现 tasks/models.py**

```python
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
```

- [ ] **Step 4: 实现 fsm/states.py**

```python
from enum import Enum


class OrchestrationState(str, Enum):
    IDLE = "idle"
    ORCHESTRATING = "orchestrating"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


VALID_TRANSITIONS: dict[OrchestrationState, set[OrchestrationState]] = {
    OrchestrationState.IDLE: {OrchestrationState.ORCHESTRATING},
    OrchestrationState.ORCHESTRATING: {OrchestrationState.DISPATCHING, OrchestrationState.FAILED},
    OrchestrationState.DISPATCHING: {OrchestrationState.EXECUTING},
    OrchestrationState.EXECUTING: {OrchestrationState.REVIEWING, OrchestrationState.ORCHESTRATING, OrchestrationState.FAILED},
    OrchestrationState.REVIEWING: {OrchestrationState.TESTING, OrchestrationState.ORCHESTRATING},
    OrchestrationState.TESTING: {OrchestrationState.COMPLETED, OrchestrationState.ORCHESTRATING},
    OrchestrationState.COMPLETED: {OrchestrationState.IDLE},
    OrchestrationState.FAILED: set(),  # 终态，不能转换
}
```

现在在 `tests/test_models.py` 末尾添加状态转换测试:

```python
from src.fsm.states import OrchestrationState, VALID_TRANSITIONS


def test_valid_transition():
    assert VALID_TRANSITIONS[OrchestrationState.IDLE] == {OrchestrationState.ORCHESTRATING}


def test_invalid_transition():
    assert OrchestrationState.COMPLETED not in VALID_TRANSITIONS[OrchestrationState.IDLE]


def test_all_states_defined():
    assert len(OrchestrationState) == 8
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_models.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add src/tasks/models.py src/fsm/states.py tests/test_models.py
git commit -m "feat: add Task/TaskStatus models and OrchestrationState FSM"
```

---

### Task 3: Config Loader

**Files:**
- Create: `src/config/loader.py`
- Create: `agents.yaml`
- Create: `tests/test_config.py`

- [ ] **Step 1: 创建 agents.yaml**

```yaml
settings:
  max_iterations: 5
  task_timeout_seconds: 300
  global_timeout_seconds: 3600

agents:
  orchestrator:
    name: "编排Agent"
    command: "claude-code-acp"
    adapter: "claude_code"
    role: "orchestrator"
    system_prompt: |
      你是项目编排专家。你只做一件事：
      1. 接收用户需求
      2. 分析需要完成的任务
      3. 将任务拆分为独立的子任务
      4. 每个子任务指定由哪个Agent执行
      输出必须是严格的JSON数组格式: [{"id":"task_1","description":"...","assigned_agent":"..."}]
      不要做任何执行工作，只拆分和指派。

  frontend-dev:
    name: "前端开发"
    command: "codex acp"
    adapter: "codex"
    role: "executor"
    system_prompt: |
      你是前端开发专家。你只负责HTML/CSS/JavaScript代码编写。
      不要做后端、数据库相关工作。完成后说明创建/修改了哪些文件。

  backend-dev:
    name: "后端开发"
    command: "claude-code-acp"
    adapter: "claude_code"
    role: "executor"
    system_prompt: |
      你是后端开发专家。你只负责API接口开发和业务逻辑实现。
      不要做前端UI工作。完成后说明创建/修改了哪些文件。

  checker:
    name: "代码审查"
    command: "gemini --acp"
    adapter: "gemini"
    role: "checker"
    system_prompt: |
      你是代码审查专家。你只负责检查代码质量和完整性。
      输出: "通过" 或 "不通过: 具体问题描述"。不要修改代码。

  tester:
    name: "测试"
    command: "codex acp"
    adapter: "codex"
    role: "tester"
    system_prompt: |
      你是测试专家。你只负责编写测试用例、运行测试、报告结果。
      不要修改业务代码。
```

- [ ] **Step 2: 编写 config loader 测试**

创建 `tests/test_config.py`:

```python
import os
import pytest
from src.config.loader import load_config, AgentConfig, Settings


def test_load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "agents.yaml")
    config = load_config(config_path)

    assert config.settings.max_iterations == 5
    assert config.settings.task_timeout_seconds == 300

    assert "orchestrator" in config.agents
    orch = config.agents["orchestrator"]
    assert orch.name == "编排Agent"
    assert orch.role == "orchestrator"

    assert "frontend-dev" in config.agents
    fe = config.agents["frontend-dev"]
    assert fe.role == "executor"

    assert "checker" in config.agents
    assert "tester" in config.agents


def test_get_agents_by_role():
    config_path = os.path.join(os.path.dirname(__file__), "..", "agents.yaml")
    config = load_config(config_path)

    executors = [a for a in config.agents.values() if a.role == "executor"]
    assert len(executors) >= 2


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")
```

- [ ] **Step 3: 运行测试验证失败**

Run: `pytest tests/test_config.py -v`
Expected: 全部 FAIL

- [ ] **Step 4: 实现 config/loader.py**

```python
from dataclasses import dataclass, field
import yaml


@dataclass
class Settings:
    max_iterations: int = 5
    task_timeout_seconds: int = 300
    global_timeout_seconds: int = 3600


@dataclass
class AgentConfig:
    name: str
    command: str
    adapter: str
    role: str  # orchestrator | executor | checker | tester
    system_prompt: str = ""
    config: dict = field(default_factory=dict)


@dataclass
class OrchestratorConfig:
    settings: Settings
    agents: dict[str, AgentConfig]


def load_config(path: str) -> OrchestratorConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    settings = Settings(**raw.get("settings", {}))

    agents = {}
    for key, data in raw.get("agents", {}).items():
        agents[key] = AgentConfig(
            name=data["name"],
            command=data["command"],
            adapter=data["adapter"],
            role=data["role"],
            system_prompt=data.get("system_prompt", ""),
            config=data.get("config", {}),
        )

    return OrchestratorConfig(settings=settings, agents=agents)
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_config.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add src/config/loader.py agents.yaml tests/test_config.py
git commit -m "feat: add YAML config loader with AgentConfig/Settings models"
```

---

### Task 4: Logger

**Files:**
- Create: `src/logger/logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: 编写 Logger 测试**

创建 `tests/test_logger.py`:

```python
import io
from src.logger.logger import Logger


def test_logger_state_transition():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_state("IDLE", "ORCHESTRATING")
    output = buf.getvalue()
    assert "IDLE" in output
    assert "ORCHESTRATING" in output


def test_logger_orch_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_orch("拆分完成: 3个任务")
    output = buf.getvalue()
    assert "编排" in output
    assert "拆分完成: 3个任务" in output


def test_logger_router_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_router("任务1 → frontend-dev")
    output = buf.getvalue()
    assert "任务1" in output
    assert "frontend-dev" in output


def test_logger_exec_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_exec("Codex", "✅ 任务1 完成: login.html")
    output = buf.getvalue()
    assert "Codex" in output
    assert "任务1 完成" in output


def test_logger_check_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_check("✅ 审核通过")
    output = buf.getvalue()
    assert "审核通过" in output


def test_logger_test_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_test("❌ 测试失败: 2/5")
    output = buf.getvalue()
    assert "测试失败" in output


def test_logger_error():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_error("连接超时")
    output = buf.getvalue()
    assert "错误" in output
    assert "连接超时" in output


def test_logger_progress():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_progress(2, 4, 1)
    output = buf.getvalue()
    assert "2/4" in output


def test_logger_completed():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_completed(3, 7, "4分59秒")
    output = buf.getvalue()
    assert "3" in output
    assert "7" in output
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_logger.py -v`
Expected: 全部 FAIL

- [ ] **Step 3: 实现 logger/logger.py**

```python
import sys
import datetime
from typing import TextIO


class Logger:
    """统一日志格式，实时终端输出。所有消息经过这里，保证可见性。"""

    def __init__(self, output: TextIO = sys.stdout):
        self.output = output

    def _write(self, tag: str, msg: str) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output.write(f"[{now}] [{tag}] {msg}\n")
        self.output.flush()

    def log_state(self, from_state: str, to_state: str, iteration: int = 1) -> None:
        self._write("状态", f"{from_state} → {to_state} (第{iteration}轮)")

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
        self._write("错误", msg)

    def log_progress(self, done: int, total: int, iteration: int) -> None:
        bar_width = 10
        filled = int(bar_width * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        self._write("进度", f"轮次{iteration} [{bar}] {done}/{total}")

    def log_completed(self, total_iterations: int, total_tasks: int, elapsed: str) -> None:
        self._write("系统", f"项目完成! 共{total_iterations}轮迭代, {total_tasks}个任务, 耗时{elapsed}")

    def log_failed(self, reason: str) -> None:
        self._write("系统", f"流程失败: {reason}")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_logger.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add src/logger/logger.py tests/test_logger.py
git commit -m "feat: add Logger with state/agent/error/progress formatted output"
```

---

### Task 5: ACPAdapter 抽象 + AgentSession

**Files:**
- Create: `src/agents/adapter.py`
- Create: `src/agents/session.py`
- Create: `tests/test_adapter.py`

- [ ] **Step 1: 编写适配器测试**

创建 `tests/test_adapter.py`:

```python
import asyncio
import pytest
from src.agents.adapter import ACPAdapter
from src.agents.session import AgentSession


class FakeAdapter(ACPAdapter):
    """测试用假适配器 —— 不启动真实子进程"""

    def __init__(self):
        self.launched = False
        self.initialized = False
        self.prompts_sent = []
        self.closed = False
        self._response_queue = asyncio.Queue()

    def get_launch_command(self) -> list[str]:
        return ["echo", "fake"]

    async def spawn(self):
        self.launched = True
        return None, None  # 不需要真实的 stdin/stdout

    async def initialize(self, writer, reader, session_config: dict) -> str:
        self.initialized = True
        self.system_prompt = session_config.get("systemPrompt", "")
        return "fake-session-001"

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        self.prompts_sent.append(prompt)

    async def read_updates(self, reader):
        yield {"type": "message", "content": "fake update"}

    async def close_session(self, writer, session_id: str) -> None:
        self.closed = True


def test_adapter_launch_command():
    adapter = FakeAdapter()
    assert adapter.get_launch_command() == ["echo", "fake"]


@pytest.mark.asyncio
async def test_adapter_lifecycle():
    adapter = FakeAdapter()
    writer, reader = await adapter.spawn()
    assert adapter.launched

    sid = await adapter.initialize(writer, reader, {"systemPrompt": "test prompt"})
    assert adapter.initialized
    assert adapter.system_prompt == "test prompt"
    assert sid == "fake-session-001"

    await adapter.send_prompt(writer, sid, "hello world")
    assert adapter.prompts_sent == ["hello world"]

    updates = [u async for u in adapter.read_updates(reader)]
    assert len(updates) == 1
    assert updates[0]["content"] == "fake update"

    await adapter.close_session(writer, sid)
    assert adapter.closed


def test_session_creation():
    config = type("AgentConfig", (), {
        "name": "测试Agent",
        "command": "echo",
        "adapter": "fake",
        "role": "executor",
        "system_prompt": "test",
    })()
    session = AgentSession(
        agent_key="test-agent",
        config=config,
    )
    assert session.agent_key == "test-agent"
    assert session.config.name == "测试Agent"
    assert session.state == "idle"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_adapter.py -v`
Expected: 全部 FAIL

- [ ] **Step 3: 实现 agents/adapter.py**

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator


class ACPAdapter(ABC):
    """所有 ACP Agent 的统一适配接口。"""

    @abstractmethod
    def get_launch_command(self) -> list[str]:
        """返回启动命令，如 ['claude-code-acp']"""
        ...

    @abstractmethod
    async def spawn(self):
        """启动子进程，返回 (writer, reader) 管道"""
        ...

    @abstractmethod
    async def initialize(self, writer, reader, session_config: dict) -> str:
        """ACP 握手：initialize → session/new，返回 session_id"""
        ...

    @abstractmethod
    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        """发送 session/prompt"""
        ...

    @abstractmethod
    async def read_updates(self, reader) -> AsyncIterator[dict]:
        """流式读取 session/update 通知"""
        ...

    @abstractmethod
    async def close_session(self, writer, session_id: str) -> None:
        """关闭 ACP 会话"""
        ...
```

- [ ] **Step 4: 实现 agents/session.py**

```python
from dataclasses import dataclass, field
from src.config.loader import AgentConfig


@dataclass
class AgentSession:
    agent_key: str
    config: AgentConfig
    state: str = "idle"
    adapter: object = None
    writer: object = None
    reader: object = None
    session_id: str = ""

    def mark_active(self) -> None:
        self.state = "active"

    def mark_done(self) -> None:
        self.state = "done"

    def mark_error(self) -> None:
        self.state = "error"
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_adapter.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add src/agents/adapter.py src/agents/session.py tests/test_adapter.py
git commit -m "feat: add ACPAdapter abstract base and AgentSession model"
```

---

### Task 6: Agent Manager

**Files:**
- Create: `src/agents/manager.py`
- Create: `tests/test_manager.py`

- [ ] **Step 1: 编写 Manager 测试**

创建 `tests/test_manager.py`:

```python
import pytest
from src.agents.manager import AgentManager
from src.agents.adapter import ACPAdapter
from src.config.loader import AgentConfig


class FakeAdapter(ACPAdapter):
    def __init__(self):
        self.launched = False
        self.initialized = False
        self.prompts = []
        self.closed_sessions = []

    def get_launch_command(self) -> list[str]:
        return ["fake"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, config):
        self.initialized = True
        return f"sid-{id(self)}"

    async def send_prompt(self, writer, sid, prompt):
        self.prompts.append(prompt)

    async def read_updates(self, reader):
        yield {"type": "message", "content": "working..."}
        yield {"type": "message", "content": "done"}

    async def close_session(self, writer, sid):
        self.closed_sessions.append(sid)


@pytest.fixture
def manager():
    return AgentManager()


@pytest.fixture
def agent_config():
    return AgentConfig(
        name="测试Agent",
        command="fake",
        adapter="fake",
        role="executor",
        system_prompt="你是测试Agent",
    )


@pytest.mark.asyncio
async def test_register_adapter(manager):
    manager.register_adapter("fake", FakeAdapter)
    assert "fake" in manager._adapters


@pytest.mark.asyncio
async def test_spawn_agent(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)
    assert session.agent_key == "test-1"
    assert session.state == "active"


@pytest.mark.asyncio
async def test_send_task(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)

    updates = []
    async for update in manager.send_task(session, "编写一个函数"):
        updates.append(update)

    assert len(updates) == 2
    assert updates[0]["content"] == "working..."
    assert updates[1]["content"] == "done"


@pytest.mark.asyncio
async def test_kill_agent(manager, agent_config):
    manager.register_adapter("fake", FakeAdapter)
    session = await manager.spawn("test-1", agent_config)
    await manager.kill(session)
    assert len(session.adapter.closed_sessions) == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_manager.py -v`
Expected: 全部 FAIL

- [ ] **Step 3: 实现 agents/manager.py**

```python
from typing import AsyncIterator
from src.agents.adapter import ACPAdapter
from src.agents.session import AgentSession
from src.config.loader import AgentConfig
from src.logger.logger import Logger


class AgentManager:
    """管理所有 ACP Agent 子进程的生命周期。"""

    def __init__(self, logger: Logger | None = None):
        self._adapters: dict[str, type[ACPAdapter]] = {}
        self._sessions: dict[str, AgentSession] = {}
        self.logger = logger

    def register_adapter(self, name: str, adapter_cls: type[ACPAdapter]) -> None:
        self._adapters[name] = adapter_cls

    async def spawn(self, agent_key: str, config: AgentConfig) -> AgentSession:
        adapter_cls = self._adapters.get(config.adapter)
        if adapter_cls is None:
            raise ValueError(f"未注册的适配器: {config.adapter}")

        adapter = adapter_cls()
        writer, reader = await adapter.spawn()

        sid = await adapter.initialize(writer, reader, {
            "cwd": ".",
            "systemPrompt": config.system_prompt,
        })

        session = AgentSession(
            agent_key=agent_key,
            config=config,
            adapter=adapter,
            writer=writer,
            reader=reader,
            session_id=sid,
        )
        session.mark_active()
        self._sessions[agent_key] = session

        if self.logger:
            self.logger.log_router(f"Agent启动: {config.name} (session: {sid})")

        return session

    async def send_task(self, session: AgentSession, prompt: str) -> AsyncIterator[dict]:
        await session.adapter.send_prompt(session.writer, session.session_id, prompt)
        async for update in session.adapter.read_updates(session.reader):
            yield update

    async def kill(self, session: AgentSession) -> None:
        await session.adapter.close_session(session.writer, session.session_id)
        if session.agent_key in self._sessions:
            del self._sessions[session.agent_key]
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/manager.py tests/test_manager.py
git commit -m "feat: add AgentManager for lifecycle management of ACP agents"
```

---

### Task 7: Task Queue

**Files:**
- Create: `src/tasks/queue.py`
- Create: `tests/test_task_queue.py`

- [ ] **Step 1: 编写 TaskQueue 测试**

创建 `tests/test_task_queue.py`:

```python
import pytest
from src.tasks.models import Task, TaskStatus
from src.tasks.queue import TaskQueue


@pytest.fixture
def queue():
    return TaskQueue()


def test_enqueue_tasks(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="agent-a"),
        Task(id="t2", description="任务2", assigned_agent="agent-b"),
    ]
    queue.enqueue(tasks)
    assert len(queue._tasks) == 2
    assert queue._tasks["t1"].status == TaskStatus.PENDING


def test_get_pending(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="agent-a"),
        Task(id="t2", description="任务2", assigned_agent="agent-b", deps=["t1"]),
    ]
    queue.enqueue(tasks)
    ready = queue.get_ready()
    assert len(ready) == 1
    assert ready[0].id == "t1"


def test_get_pending_with_deps_satisfied(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="agent-a"),
        Task(id="t2", description="任务2", assigned_agent="agent-b", deps=["t1"]),
    ]
    queue.enqueue(tasks)
    queue.mark_done("t1", "完成")
    ready = queue.get_ready()
    assert len(ready) == 1
    assert ready[0].id == "t2"


def test_mark_done(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="agent-a")]
    queue.enqueue(tasks)
    queue.mark_running("t1")
    assert queue._tasks["t1"].status == TaskStatus.RUNNING
    queue.mark_done("t1", "完成了")
    assert queue._tasks["t1"].status == TaskStatus.DONE
    assert queue._tasks["t1"].result == "完成了"


def test_mark_failed(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="agent-a")]
    queue.enqueue(tasks)
    queue.mark_failed("t1", "超时")
    assert queue._tasks["t1"].status == TaskStatus.FAILED


def test_all_done(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    assert not queue.all_done()
    queue.mark_done("t1", "ok")
    assert not queue.all_done()
    queue.mark_done("t2", "ok")
    assert queue.all_done()


def test_has_failed(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    assert not queue.has_failed()
    queue.mark_failed("t2", "error")
    assert queue.has_failed()


def test_status_summary(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
        Task(id="t3", description="任务3", assigned_agent="c"),
        Task(id="t4", description="任务4", assigned_agent="d"),
    ]
    queue.enqueue(tasks)
    queue.mark_done("t1", "ok")
    queue.mark_done("t2", "ok")
    summary = queue.status_summary()
    assert "2/4" in summary


def test_get_done_tasks(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    queue.mark_done("t1", "result1")
    done = queue.get_done_tasks()
    assert len(done) == 1
    assert done[0].id == "t1"


def test_get_failed_tasks(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="a")]
    queue.enqueue(tasks)
    queue.mark_failed("t1", "error")
    failed = queue.get_failed_tasks()
    assert len(failed) == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_task_queue.py -v`
Expected: 全部 FAIL

- [ ] **Step 3: 实现 tasks/queue.py**

```python
from src.tasks.models import Task, TaskStatus


class TaskQueue:
    """管理任务的入队、分发、状态追踪。"""

    def __init__(self):
        self._tasks: dict[str, Task] = {}

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

    def mark_running(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].mark_running()

    def mark_done(self, task_id: str, result: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].mark_done(result)

    def mark_failed(self, task_id: str, error: str) -> None:
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_task_queue.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add src/tasks/queue.py tests/test_task_queue.py
git commit -m "feat: add TaskQueue with dependency resolution and progress tracking"
```

---

### Task 8: FSM Engine（线性流程）

**Files:**
- Create: `src/fsm/engine.py`
- Create: `tests/test_fsm.py`

- [ ] **Step 1: 编写 FSM Engine 测试**

创建 `tests/test_fsm.py`:

```python
import asyncio
import pytest
from src.fsm.states import OrchestrationState
from src.fsm.engine import OrchestrationFSM
from src.tasks.models import Task, TaskStatus
from src.tasks.queue import TaskQueue
from src.agents.manager import AgentManager
from src.agents.adapter import ACPAdapter
from src.config.loader import AgentConfig, Settings, OrchestratorConfig
from src.logger.logger import Logger
import io


class EchoAdapter(ACPAdapter):
    """回显适配器 — 收到什么就返回什么，模拟真实Agent行为"""

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
    """构建测试用配置"""
    return OrchestratorConfig(
        settings=Settings(max_iterations=3),
        agents={
            "orchestrator": AgentConfig(
                name="编排", command="echo", adapter="echo",
                role="orchestrator",
                system_prompt="拆分任务，输出JSON",
            ),
            "worker": AgentConfig(
                name="执行", command="echo", adapter="echo",
                role="executor",
                system_prompt="执行任务",
            ),
            "checker": AgentConfig(
                name="检查", command="echo", adapter="echo",
                role="checker",
                system_prompt="检查代码",
            ),
            "tester": AgentConfig(
                name="测试", command="echo", adapter="echo",
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


@pytest.mark.asyncio
async def test_fsm_parse_orchestrator_output():
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


@pytest.mark.asyncio
async def test_fsm_parse_invalid_json(fsm):
    tasks = fsm._parse_tasks("这不是JSON")
    assert tasks == []


@pytest.mark.asyncio
async def test_fsm_parse_json_with_markdown_wrapper():
    fsm = OrchestrationFSM(config=make_test_config(), manager=AgentManager(), logger=Logger(output=io.StringIO()))
    text = '好的，我拆分为以下任务:\n```json\n[{"id":"t1","description":"测试","assigned_agent":"worker"}]\n```'
    tasks = fsm._parse_tasks(text)
    assert len(tasks) == 1
    assert tasks[0].id == "t1"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_fsm.py -v`
Expected: 全部 FAIL

- [ ] **Step 3: 实现 fsm/engine.py**

```python
import json
import re
import time
import asyncio
from src.fsm.states import OrchestrationState, VALID_TRANSITIONS
from src.tasks.models import Task
from src.tasks.queue import TaskQueue
from src.agents.manager import AgentManager
from src.config.loader import OrchestratorConfig
from src.logger.logger import Logger


class OrchestrationFSM:
    """编排状态机核心 — 掌控整个编排流程的状态转换。"""

    def __init__(
        self,
        config: OrchestratorConfig,
        manager: AgentManager,
        logger: Logger,
    ):
        self.config = config
        self.manager = manager
        self.logger = logger
        self.state = OrchestrationState.IDLE
        self.iteration = 0
        self.task_queue = TaskQueue()
        self.completed_iterations: list[dict] = []

    def _transition(self, new_state: OrchestrationState) -> None:
        allowed = VALID_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(f"非法状态转换: {self.state.value} → {new_state.value}")
        old = self.state
        self.state = new_state
        self.logger.log_state(old.value, new_state.value, self.iteration or 1)

    def _parse_tasks(self, text: str) -> list[Task]:
        """从编排Agent输出中提取JSON任务列表。"""
        # 尝试匹配 ```json ... ``` 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        json_str = json_match.group(1) if json_match else text

        # 尝试匹配 JSON 数组
        arr_match = re.search(r'\[[\s\S]*\]', json_str)
        if arr_match:
            json_str = arr_match.group(0)

        try:
            raw_tasks = json.loads(json_str)
            if not isinstance(raw_tasks, list):
                return []
            tasks = []
            for t in raw_tasks:
                if isinstance(t, dict) and "id" in t and "description" in t and "assigned_agent" in t:
                    tasks.append(Task(
                        id=t["id"],
                        description=t["description"],
                        assigned_agent=t["assigned_agent"],
                        deps=t.get("deps", []),
                    ))
            return tasks
        except (json.JSONDecodeError, TypeError):
            return []

    async def _orchestrate(self, requirement: str, fail_context: str = "") -> list[Task]:
        """调用编排Agent拆分任务。"""
        self._transition(OrchestrationState.ORCHESTRATING)
        self.iteration += 1

        orch_config = self.config.agents.get("orchestrator")
        if orch_config is None:
            raise ValueError("agents.yaml中缺少orchestrator配置")

        session = await self.manager.spawn("orchestrator", orch_config)

        context = f"需求: {requirement}"
        if fail_context:
            context = fail_context

        self.logger.log_orch(f"接收需求: {requirement[:80]}...")
        full_response = ""

        async for update in self.manager.send_task(session, context):
            content = update.get("content", "")
            if content:
                self.logger.log_orch(content)
                full_response += content

        await self.manager.kill(session)

        tasks = self._parse_tasks(full_response)
        if not tasks:
            self.logger.log_error("编排Agent输出无法解析")
            return []

        self.logger.log_orch(f"拆分结果: {len(tasks)}个任务")
        for task in tasks:
            self.logger.log_router(f"  └─ {task.id} → {task.assigned_agent}")

        return tasks

    async def _dispatch(self, tasks: list[Task]) -> None:
        """将任务分发给执行Agent。"""
        self._transition(OrchestrationState.DISPATCHING)
        self.task_queue.clear()
        self.task_queue.enqueue(tasks)

    async def _execute(self) -> None:
        """并行执行所有任务。"""
        self._transition(OrchestrationState.EXECUTING)

        async def execute_one(task: Task):
            agent_config = self.config.agents.get(task.assigned_agent)
            if agent_config is None:
                self.task_queue.mark_failed(task.id, f"未知Agent: {task.assigned_agent}")
                return

            self.task_queue.mark_running(task.id)
            session = await self.manager.spawn(f"exec-{task.id}", agent_config)
            self.logger.log_router(f"任务 {task.id} → {agent_config.name}")

            try:
                full_response = ""
                async for update in self.manager.send_task(session, task.description):
                    content = update.get("content", "")
                    if content:
                        self.logger.log_exec(agent_config.name, content)
                        full_response += content

                self.task_queue.mark_done(task.id, full_response.strip())
                self.logger.log_exec(agent_config.name, f"✅ {task.id} 完成")
            except Exception as e:
                self.task_queue.mark_failed(task.id, str(e))
                self.logger.log_error(f"{task.id} 失败: {e}")
            finally:
                await self.manager.kill(session)

            self.logger.log_progress(
                len(self.task_queue.get_done_tasks()) + len(self.task_queue.get_failed_tasks()),
                len(self.task_queue._tasks),
                self.iteration,
            )

        # Phase 1: 按顺序执行（Phase 2 升级为并行）
        ready = self.task_queue.get_ready()
        while ready:
            for task in ready:
                await execute_one(task)
            ready = self.task_queue.get_ready()

    async def _review(self) -> bool:
        """调用检查Agent审核。"""
        self._transition(OrchestrationState.REVIEWING)

        done_tasks = self.task_queue.get_done_tasks()
        review_text = "请审核以下任务产出:\n\n"
        for task in done_tasks:
            review_text += f"## {task.id}: {task.description}\n{task.result}\n\n"

        checker_config = self.config.agents.get("checker")
        if checker_config is None:
            self.logger.log_check("无检查Agent配置，跳过审核")
            return True

        session = await self.manager.spawn("checker", checker_config)
        full_response = ""

        async for update in self.manager.send_task(session, review_text):
            content = update.get("content", "")
            if content:
                self.logger.log_check(content)
                full_response += content

        await self.manager.kill(session)

        passed = "通过" in full_response and "不通过" not in full_response
        if not passed:
            self.logger.log_check("⚠️ 审核不通过")
        return passed

    async def _test(self) -> bool:
        """调用测试Agent验证。"""
        self._transition(OrchestrationState.TESTING)

        done_tasks = self.task_queue.get_done_tasks()
        test_text = "请测试以下代码产出:\n\n"
        for task in done_tasks:
            test_text += f"## {task.id}: {task.description}\n{task.result}\n\n"

        tester_config = self.config.agents.get("tester")
        if tester_config is None:
            self.logger.log_test("无测试Agent配置，跳过测试")
            return True

        session = await self.manager.spawn("tester", tester_config)
        full_response = ""

        async for update in self.manager.send_task(session, test_text):
            content = update.get("content", "")
            if content:
                self.logger.log_test(content)
                full_response += content

        await self.manager.kill(session)

        passed = "通过" in full_response and "失败" not in full_response
        if not passed:
            self.logger.log_test("❌ 测试不通过")
        return passed

    async def run(self, requirement: str) -> dict:
        """主入口：运行完整的编排流程。"""
        start_time = time.time()

        try:
            self._transition(OrchestrationState.ORCHESTRATING)
            self.iteration += 1

            # 编排
            tasks = await self._orchestrate(requirement)
            if not tasks:
                self._transition(OrchestrationState.FAILED)
                return {"status": "failed", "reason": "编排Agent输出解析失败"}

            # 分发
            await self._dispatch(tasks)

            # 执行
            await self._execute()

            if self.task_queue.has_failed():
                self._transition(OrchestrationState.FAILED)
                return {"status": "failed", "reason": "任务执行失败"}

            # 检查
            review_ok = await self._review()
            if not review_ok:
                self._transition(OrchestrationState.FAILED)
                return {"status": "failed", "reason": "检查不通过"}

            # 测试
            test_ok = await self._test()
            if not test_ok:
                self._transition(OrchestrationState.FAILED)
                return {"status": "failed", "reason": "测试不通过"}

            # 完成
            self._transition(OrchestrationState.COMPLETED)
            elapsed = f"{time.time() - start_time:.2f}秒"
            total_tasks = len(self.task_queue._tasks)
            self.logger.log_completed(self.iteration, total_tasks, elapsed)

            return {
                "status": "completed",
                "iterations": self.iteration,
                "total_tasks": total_tasks,
                "elapsed": elapsed,
            }

        except Exception as e:
            self._transition(OrchestrationState.FAILED)
            self.logger.log_failed(str(e))
            return {"status": "failed", "reason": str(e)}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_fsm.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add src/fsm/engine.py tests/test_fsm.py
git commit -m "feat: add OrchestrationFSM engine with linear flow (no rework yet)"
```

---

### Task 9: Mock Adapter（测试用）

**Files:**
- Create: `src/agents/adapters/mock.py`

- [ ] **Step 1: 实现 Mock Adapter**

```python
"""Mock ACP Adapter — 用于测试，不启动真实子进程。"""

from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


class MockAdapter(ACPAdapter):
    """模拟 ACP Agent，返回预设响应。"""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["任务完成"]
        self._idx = 0
        self.launched = False
        self.initialized = False
        self.prompts: list[str] = []
        self.closed = False
        self._system_prompt = ""

    def get_launch_command(self) -> list[str]:
        return ["mock"]

    async def spawn(self):
        self.launched = True
        return None, None

    async def initialize(self, writer, reader, session_config: dict) -> str:
        self.initialized = True
        self._system_prompt = session_config.get("systemPrompt", "")
        return "mock-session-001"

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        self.prompts.append(prompt)

    async def read_updates(self, reader) -> AsyncIterator[dict]:
        for resp in self.responses:
            yield {"type": "message", "content": resp}
        self._idx = 0

    async def close_session(self, writer, session_id: str) -> None:
        self.closed = True
```

- [ ] **Step 2: Commit**

```bash
git add src/agents/adapters/mock.py src/agents/adapters/__init__.py
git commit -m "feat: add MockAdapter for testing without real agent processes"
```

---

### Task 10: CLI 入口

**Files:**
- Create: `src/main.py`
- Modify: `pyproject.toml`（添加 scripts 入口）

- [ ] **Step 1: 实现 CLI 入口**

创建 `src/main.py`:

```python
"""ACP Orchestrator CLI — 多Agent编排框架入口。"""

import argparse
import asyncio
import os
import sys
from src.config.loader import load_config
from src.fsm.engine import OrchestrationFSM
from src.fsm.states import OrchestrationState
from src.agents.manager import AgentManager
from src.agents.adapters.mock import MockAdapter
from src.logger.logger import Logger


def get_default_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "agents.yaml")


async def main_async(requirement: str, config_path: str) -> int:
    logger = Logger()

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        logger.log_error(f"配置文件不存在: {config_path}")
        return 1

    manager = AgentManager(logger=logger)

    # 注册适配器 — 先注册 mock，后续 Phase 3 添加真实适配器
    manager.register_adapter("mock", MockAdapter)
    manager.register_adapter("claude_code", MockAdapter)  # TODO: Phase 3 替换为真实适配器
    manager.register_adapter("codex", MockAdapter)
    manager.register_adapter("gemini", MockAdapter)
    manager.register_adapter("echo", MockAdapter)

    fsm = OrchestrationFSM(config=config, manager=manager, logger=logger)
    result = await fsm.run(requirement)

    if result["status"] == "completed":
        print(f"\n{'='*50}")
        print(f"状态: 完成")
        print(f"迭代: {result['iterations']}轮")
        print(f"任务: {result['total_tasks']}个")
        print(f"耗时: {result['elapsed']}")
        return 0
    else:
        print(f"\n{'='*50}")
        print(f"状态: 失败")
        print(f"原因: {result['reason']}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ACP Orchestrator — 多Agent编排框架",
    )
    parser.add_argument(
        "requirement",
        nargs="?",
        help="需求描述 (如: '开发一个登录页面')",
    )
    parser.add_argument(
        "-c", "--config",
        default=get_default_config_path(),
        help=f"配置文件路径 (默认: agents.yaml)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="检查配置文件是否合法",
    )

    args = parser.parse_args()

    if args.check_config:
        try:
            config = load_config(args.config)
            print(f"配置文件: {args.config}")
            print(f"Agent数量: {len(config.agents)}")
            for key, agent in config.agents.items():
                print(f"  - {key}: {agent.name} ({agent.role}) [{agent.adapter}]")
            print("配置合法。")
            return 0
        except Exception as e:
            print(f"配置错误: {e}")
            return 1

    if not args.requirement:
        parser.print_help()
        return 1

    return asyncio.run(main_async(args.requirement, args.config))


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 更新 pyproject.toml 添加 CLI 入口**

在 `[project]` 小节后添加:

```toml
[project.scripts]
acp-orch = "src.main:main"
```

- [ ] **Step 3: 验证 CLI 可运行**

Run: `python -m src.main --check-config`
Expected: 显示 agents.yaml 中的 Agent 列表

- [ ] **Step 4: Commit**

```bash
git add src/main.py pyproject.toml
git commit -m "feat: add CLI entry point with --check-config"
```

---

### Task 11: 集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

创建 `tests/test_integration.py`:

```python
"""端到端集成测试 — 使用 MockAdapter 模拟完整编排流程。"""

import io
import pytest
from src.fsm.engine import OrchestrationFSM
from src.agents.manager import AgentManager
from src.agents.adapters.mock import MockAdapter
from src.config.loader import AgentConfig, Settings, OrchestratorConfig
from src.logger.logger import Logger


def make_e2e_config():
    """构建端到端测试配置，所有Agent使用MockAdapter。"""
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
    """编排Agent的Mock — 返回标准JSON任务列表。"""
    def __init__(self):
        super().__init__(responses=[
            '好的，我拆分为以下任务:\n```json\n[{"id":"task_1","description":"编写登录页面","assigned_agent":"worker"},{"id":"task_2","description":"编写API","assigned_agent":"worker"}]\n```'
        ])


class WorkerMock(MockAdapter):
    """执行Agent的Mock — 返回完成信息。"""
    def __init__(self):
        super().__init__(responses=["工作中...", "任务完成，已创建文件"])


class CheckerPassMock(MockAdapter):
    """检查Agent的Mock — 返回通过。"""
    def __init__(self):
        super().__init__(responses=["所有任务审核通过，代码质量良好"])


class TesterPassMock(MockAdapter):
    """测试Agent的Mock — 返回通过。"""
    def __init__(self):
        super().__init__(responses=["测试全部通过 3/3"])


@pytest.mark.asyncio
async def test_full_happy_path():
    """端到端测试：编排→执行→检查→测试 全部通过。"""
    buf = io.StringIO()
    logger = Logger(output=buf)
    config = make_e2e_config()
    manager = AgentManager(logger=logger)

    # 注册专用Mock
    manager.register_adapter("mock", WorkerMock)  # 默认mock

    fsm = OrchestrationFSM(config=config, manager=manager, logger=logger)

    # 注入专用Mock到FSM的spawn流程
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
    assert "IDLE" in output
    assert "ORCHESTRATING" in output
    assert "DISPATCHING" in output
    assert "EXECUTING" in output
    assert "REVIEWING" in output
    assert "TESTING" in output
    assert "COMPLETED" in output
    assert "项目完成" in output
```

- [ ] **Step 2: 运行集成测试验证通过**

Run: `pytest tests/test_integration.py -v`
Expected: PASS（完整流程走通）

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test for happy path"
```

---

## Phase 2: 循环迭代 + 多 Agent

**目标:** 返工循环 + 并行执行 + 超时保护

### Task 12: rebuild_context() 上下文组装

**Files:**
- Create: `src/fsm/context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: 编写测试**

```python
import pytest
from src.fsm.context import rebuild_context
from src.tasks.models import Task


def test_rebuild_context_basic():
    tasks = [
        Task(id="t1", description="前端页面", assigned_agent="worker"),
        Task(id="t2", description="后端API", assigned_agent="worker"),
    ]
    tasks[0].mark_done("完成了login.html")
    tasks[1].mark_done("完成了api.py")

    ctx = rebuild_context(
        original_requirement="开发登录功能",
        completed_tasks=tasks,
        failed_info="测试失败: test_login返回500",
        iteration=2,
    )

    assert "开发登录功能" in ctx
    assert "第2轮" in ctx
    assert "已完成" in ctx
    assert "t1" in ctx
    assert "t2" in ctx
    assert "login.html" in ctx
    assert "测试失败" in ctx
    assert "不要重新分配" in ctx
```

- [ ] **Step 2: 实现 fsm/context.py**

```python
from src.tasks.models import Task


def rebuild_context(
    original_requirement: str,
    completed_tasks: list[Task],
    failed_info: str,
    iteration: int,
) -> str:
    parts = [
        f"## 原始需求\n{original_requirement}\n",
        f"## 当前迭代: 第{iteration}轮\n",
        "## 已完成的任务 (不要重新分配)\n",
    ]
    for t in completed_tasks:
        parts.append(f"- ✅ {t.id} [{t.assigned_agent}]: {t.description}\n  产出: {t.result}\n")

    parts.append(f"\n## 失败/问题 (需要重新处理)\n{failed_info}\n")
    parts.append("\n请分析问题，只拆分需要修复的新任务。输出JSON格式。")

    return "\n".join(parts)
```

- [ ] **Step 3: 运行测试通过后 Commit**

---

### Task 13: FSM 返工路径

**Files:**
- Modify: `src/fsm/engine.py` — 修改 `run()` 方法支持循环迭代

- [ ] **Step 1: 重写 FSM.run() 支持循环**

```python
async def run(self, requirement: str) -> dict:
    start_time = time.time()

    try:
        self._transition(OrchestrationState.ORCHESTRATING)
        self.iteration += 1

        # 编排
        tasks = await self._orchestrate(requirement)
        if not tasks:
            self._transition(OrchestrationState.FAILED)
            return {"status": "failed", "reason": "编排Agent输出解析失败"}

        while self.iteration <= self.config.settings.max_iterations:
            # 分发
            await self._dispatch(tasks)

            # 执行
            await self._execute()

            if self.task_queue.has_failed():
                done = self.task_queue.get_done_tasks()
                failed = self.task_queue.get_failed_tasks()
                fail_info = "以下任务执行失败:\n"
                for t in failed:
                    fail_info += f"- ❌ {t.id}: {t.error}\n"

                context = rebuild_context(requirement, done, fail_info, self.iteration)
                self.logger.log_error(f"返工: 第{self.iteration}轮有失败任务")
                tasks = await self._orchestrate(requirement, fail_context=context)
                if not tasks:
                    self._transition(OrchestrationState.FAILED)
                    return {"status": "failed", "reason": "编排Agent返工解析失败"}
                continue

            # 检查
            review_ok = await self._review()
            if not review_ok:
                done = self.task_queue.get_done_tasks()
                fail_info = "检查不通过: 代码存在问题需要修复"
                context = rebuild_context(requirement, done, fail_info, self.iteration)
                tasks = await self._orchestrate(requirement, fail_context=context)
                if not tasks:
                    self._transition(OrchestrationState.FAILED)
                    return {"status": "failed", "reason": "编排Agent返工解析失败"}
                continue

            # 测试
            test_ok = await self._test()
            if not test_ok:
                done = self.task_queue.get_done_tasks()
                fail_info = "测试不通过: 部分测试用例失败"
                context = rebuild_context(requirement, done, fail_info, self.iteration)
                tasks = await self._orchestrate(requirement, fail_context=context)
                if not tasks:
                    self._transition(OrchestrationState.FAILED)
                    return {"status": "failed", "reason": "编排Agent返工解析失败"}
                continue

            # 全部通过
            self._transition(OrchestrationState.COMPLETED)
            elapsed = f"{time.time() - start_time:.2f}秒"
            total_tasks_done = len(self.task_queue.get_done_tasks())
            self.logger.log_completed(self.iteration, total_tasks_done, elapsed)
            return {
                "status": "completed",
                "iterations": self.iteration,
                "total_tasks": total_tasks_done,
                "elapsed": elapsed,
            }

        # 超出最大迭代次数
        self._transition(OrchestrationState.FAILED)
        return {"status": "failed", "reason": f"超过最大迭代次数({self.config.settings.max_iterations})"}

    except Exception as e:
        self._transition(OrchestrationState.FAILED)
        self.logger.log_failed(str(e))
        return {"status": "failed", "reason": str(e)}
```

- [ ] **Step 2: 更新集成测试验证返工路径** — 测试检查不通过→返工→最终通过

- [ ] **Step 3: Commit**

---

### Task 14: 并行执行多 Agent

**Files:**
- Modify: `src/fsm/engine.py` — `_execute()` 方法

- [ ] **Step 1: 将 `_execute()` 改为并行**

```python
async def _execute(self) -> None:
    self._transition(OrchestrationState.EXECUTING)

    async def execute_one(task: Task):
        # ... 同 Phase 1 的 execute_one ...

    # 改为并行: 所有ready任务同时启动
    ready = self.task_queue.get_ready()
    while ready:
        await asyncio.gather(*[execute_one(t) for t in ready])
        ready = self.task_queue.get_ready()
```

- [ ] **Step 2: 编写并行执行测试**

```python
@pytest.mark.asyncio
async def test_parallel_execution():
    """验证多个任务可以并行执行。"""
    # 使用 MockAdapter 的不同响应时间验证并行
    pass
```

- [ ] **Step 3: Commit**

---

### Task 15: 超时保护 + 迭代上限

**Files:**
- Modify: `src/fsm/engine.py`

- [ ] **Step 1: 添加 asyncio.wait_for 超时**

```python
async def execute_one_with_timeout(task: Task, timeout: int):
    try:
        await asyncio.wait_for(execute_one(task), timeout=timeout)
    except asyncio.TimeoutError:
        self.task_queue.mark_failed(task.id, f"超时({timeout}秒)")
        self.logger.log_error(f"{task.id} 超时")
```

- [ ] **Step 2: 全局超时**

在 `run()` 中添加全局超时逻辑。

- [ ] **Step 3: Commit**

---

## Phase 3: 多 Agent 适配 + 健壮性

**目标:** 实现全部 17 个 Agent 的适配器 + 完整容错

### Task 16: 真实 ACP 适配器（统一模板）

所有 17 个适配器结构完全相同，只是 `get_launch_command()` 返回值不同。下面是模板和两个具体示例。

**Files:**
- Create: `src/agents/adapters/real.py` — 真实 ACP 子进程适配器基类

**所有适配器共享的 `RealACPAdapter` 基类:**

```python
"""真实 ACP 适配器 — 通过 subprocess 启动 Agent 并通过 stdin/stdout 通信。"""

import asyncio
import json
from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


class RealACPAdapter(ACPAdapter):
    """真实 ACP Agent 适配器基类。子类只需覆盖 get_launch_command()。"""

    def get_launch_command(self) -> list[str]:
        raise NotImplementedError

    async def spawn(self):
        cmd = self.get_launch_command()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc.stdin, proc.stdout

    async def initialize(self, writer, reader, session_config: dict) -> str:
        # Step 1: initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.11.0",
                "clientInfo": {"name": "acp-orchestrator", "version": "0.1.0"},
                "capabilities": {"fs": {}, "terminal": {}},
            },
        }
        await self._send_json(writer, init_msg)
        resp = await self._read_json(reader)
        # 忽略 initialize 响应内容

        # Step 2: session/new
        session_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {
                "cwd": ".",
                "systemPrompt": session_config.get("systemPrompt", ""),
            },
        }
        await self._send_json(writer, session_msg)
        resp = await self._read_json(reader)
        return resp.get("result", {}).get("sessionId", "unknown")

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": prompt}],
            },
        }
        await self._send_json(writer, msg)

    async def read_updates(self, reader) -> AsyncIterator[dict]:
        while True:
            try:
                line = await asyncio.wait_for(reader.readline(), timeout=300)
                if not line:
                    break
                msg = json.loads(line.decode("utf-8").strip())
                if "result" in msg and "id" in msg:
                    # 这是 session/prompt 的最终响应，任务完成
                    result = msg.get("result", {})
                    yield {"type": "result", "content": result.get("message", {}).get("text", str(result))}
                    break
                elif msg.get("method") == "session/update":
                    update = msg.get("params", {}).get("update", {})
                    yield update
            except asyncio.TimeoutError:
                yield {"type": "error", "content": "读取超时"}
                break

    async def close_session(self, writer, session_id: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/close",
            "params": {"sessionId": session_id},
        }
        try:
            await self._send_json(writer, msg)
        except Exception:
            pass

    async def _send_json(self, writer, data: dict) -> None:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        writer.write(line.encode("utf-8"))
        await writer.drain()

    async def _read_json(self, reader) -> dict:
        line = await reader.readline()
        if not line:
            raise EOFError("Agent 子进程意外退出")
        return json.loads(line.decode("utf-8").strip())
```

**具体适配器示例 — 每个只需一行启动命令:**

```python
# src/agents/adapters/claude_code.py
from src.agents.adapters.real import RealACPAdapter

class ClaudeCodeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["claude-code-acp"]


# src/agents/adapters/codex.py
from src.agents.adapters.real import RealACPAdapter

class CodexAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["npx", "@zed-industries/codex-acp"]


# src/agents/adapters/pi.py
from src.agents.adapters.real import RealACPAdapter

class PiAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["pi-acp"]


# src/agents/adapters/reasonix.py
from src.agents.adapters.real import RealACPAdapter

class ReasonixAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["npx", "reasonix", "--acp"]


# src/agents/adapters/opencode.py
from src.agents.adapters.real import RealACPAdapter

class OpenCodeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["opencode", "acp"]
```

其余适配器（gemini, copilot, goose, cline, auggie, kiro, qwen_code, vibe, droid, qoder, hermes, openhands）结构完全相同。

**在 AgentManager 中注册所有适配器:**

```python
# 在 main.py 或 manager.py 初始化时:
from src.agents.adapters.claude_code import ClaudeCodeAdapter
from src.agents.adapters.codex import CodexAdapter
from src.agents.adapters.gemini import GeminiAdapter
# ... 等

manager.register_adapter("claude_code", ClaudeCodeAdapter)
manager.register_adapter("codex", CodexAdapter)
manager.register_adapter("gemini", GeminiAdapter)
# ... 等
```

- [ ] **Step 1: 实现 `RealACPAdapter` 基类**
- [ ] **Step 2: 实现全部 17 个适配器 (每个 5 行代码)**
- [ ] **Step 3: 在 main.py 中注册所有适配器**
- [ ] **Step 4: 编写适配器参数化测试** — 验证每个适配器的 `get_launch_command()` 返回正确的命令列表
- [ ] **Step 5: Commit**

---

## Phase 4: OpenHands 集成

**目标:** 作为 OpenHands 插件运行

### Task 21: OpenHands 插件入口

**Files:**
- Create: `src/openhands/plugin.py`

- [ ] 实现 OpenHands 插件标准接口，将 `OrchestrationFSM.run()` 嵌入 OpenHands 的 Agent 生命周期
- [ ] 在 OpenHands UI 中展示编排进度

---

## 总结

| Phase | 任务数 | 产出 |
|---|---|---|
| Phase 1 | 11 | 可运行的 MVP — 线性编排流程 |
| Phase 2 | 4 | 循环迭代 + 并行执行 + 超时保护 |
| Phase 3 | 5+ | 17个Agent适配器 + 崩溃恢复 |
| Phase 4 | 1+ | OpenHands 插件集成 |
