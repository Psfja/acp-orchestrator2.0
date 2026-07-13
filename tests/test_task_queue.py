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


@pytest.mark.asyncio
async def test_get_pending_with_deps_satisfied(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="agent-a"),
        Task(id="t2", description="任务2", assigned_agent="agent-b", deps=["t1"]),
    ]
    queue.enqueue(tasks)
    await queue.mark_done("t1", "完成")
    ready = queue.get_ready()
    assert len(ready) == 1
    assert ready[0].id == "t2"


@pytest.mark.asyncio
async def test_mark_done(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="agent-a")]
    queue.enqueue(tasks)
    await queue.mark_running("t1")
    assert queue._tasks["t1"].status == TaskStatus.RUNNING
    await queue.mark_done("t1", "完成了")
    assert queue._tasks["t1"].status == TaskStatus.DONE
    assert queue._tasks["t1"].result == "完成了"


@pytest.mark.asyncio
async def test_mark_failed(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="agent-a")]
    queue.enqueue(tasks)
    await queue.mark_failed("t1", "超时")
    assert queue._tasks["t1"].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_all_done(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    assert not queue.all_done()
    await queue.mark_done("t1", "ok")
    assert not queue.all_done()
    await queue.mark_done("t2", "ok")
    assert queue.all_done()


@pytest.mark.asyncio
async def test_has_failed(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    assert not queue.has_failed()
    await queue.mark_failed("t2", "error")
    assert queue.has_failed()


@pytest.mark.asyncio
async def test_status_summary(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
        Task(id="t3", description="任务3", assigned_agent="c"),
        Task(id="t4", description="任务4", assigned_agent="d"),
    ]
    queue.enqueue(tasks)
    await queue.mark_done("t1", "ok")
    await queue.mark_done("t2", "ok")
    summary = queue.status_summary()
    assert "2/4" in summary


@pytest.mark.asyncio
async def test_get_done_tasks(queue):
    tasks = [
        Task(id="t1", description="任务1", assigned_agent="a"),
        Task(id="t2", description="任务2", assigned_agent="b"),
    ]
    queue.enqueue(tasks)
    await queue.mark_done("t1", "result1")
    done = queue.get_done_tasks()
    assert len(done) == 1
    assert done[0].id == "t1"


@pytest.mark.asyncio
async def test_get_failed_tasks(queue):
    tasks = [Task(id="t1", description="任务1", assigned_agent="a")]
    queue.enqueue(tasks)
    await queue.mark_failed("t1", "error")
    failed = queue.get_failed_tasks()
    assert len(failed) == 1
