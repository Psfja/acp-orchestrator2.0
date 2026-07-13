"""验证交互式 REPL 的核心功能。"""
import asyncio
import io
import pytest
from unittest.mock import patch
from src.cli.repl import OrchestratorREPL
from src.cli.display import Display


def test_display_banner():
    buf = io.StringIO()
    d = Display()
    # 验证不会崩溃
    d.banner()
    d.show_help()
    d.separator()


def test_display_result_card():
    buf = io.StringIO()
    d = Display()
    d.result_card({"status": "completed", "iterations": 2, "total_tasks": 5, "elapsed": "10.0秒"})


def test_display_system_messages():
    buf = io.StringIO()
    d = Display()
    d.success("完成")
    d.warn("注意")
    d.error("失败")
    d.system_info("加载配置...")
    d.progress_bar(3, 5, "任务中")


def test_repl_creation():
    repl = OrchestratorREPL()
    assert repl.turn == 0
    assert repl.config is not None
    assert len(repl.session_history) == 0


@pytest.mark.asyncio
async def test_repl_run_requirement():
    repl = OrchestratorREPL()
    result = await repl.run_requirement("写一个hello world")
    assert result["turn"] == 1
    assert result["status"] in ("completed", "failed")
    assert "elapsed" in result
    assert len(repl.session_history) == 1


def test_repl_handle_help():
    repl = OrchestratorREPL()
    result = asyncio.run(repl._handle_command("/help"))
    assert result is True


def test_repl_handle_exit():
    repl = OrchestratorREPL()
    result = asyncio.run(repl._handle_command("/exit"))
    assert result is False


def test_repl_handle_clear():
    repl = OrchestratorREPL()
    repl.turn = 5
    repl.session_history = [{"status": "completed"}]
    result = asyncio.run(repl._handle_command("/clear"))
    assert result is True
    assert repl.turn == 0
    assert len(repl.session_history) == 0


def test_repl_handle_unknown_command():
    repl = OrchestratorREPL()
    result = asyncio.run(repl._handle_command("/foobar"))
    assert result is True
