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


from src.fsm.states import OrchestrationState, VALID_TRANSITIONS


def test_valid_transition():
    assert VALID_TRANSITIONS[OrchestrationState.IDLE] == {OrchestrationState.ORCHESTRATING}


def test_invalid_transition():
    assert OrchestrationState.COMPLETED not in VALID_TRANSITIONS[OrchestrationState.IDLE]


def test_all_states_defined():
    assert len(OrchestrationState) == 8
