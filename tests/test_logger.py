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
    logger.log_exec("Codex", "任务1 完成: login.html")
    output = buf.getvalue()
    assert "Codex" in output
    assert "任务1 完成" in output


def test_logger_check_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_check("审核通过")
    output = buf.getvalue()
    assert "审核通过" in output


def test_logger_test_message():
    buf = io.StringIO()
    logger = Logger(output=buf)
    logger.log_test("测试失败: 2/5")
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
