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


def test_rebuild_context_empty_tasks():
    ctx = rebuild_context(
        original_requirement="简单需求",
        completed_tasks=[],
        failed_info="执行失败",
        iteration=1,
    )
    assert "简单需求" in ctx
    assert "第1轮" in ctx
    assert "执行失败" in ctx


def test_rebuild_context_preserves_agent_info():
    task = Task(id="t1", description="写API", assigned_agent="backend-dev")
    task.mark_done("创建了auth.py")

    ctx = rebuild_context("需求", [task], "检查不通过", 3)
    assert "backend-dev" in ctx
    assert "auth.py" in ctx
