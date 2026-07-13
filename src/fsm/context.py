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
        parts.append(f"- OK {t.id} [{t.assigned_agent}]: {t.description}\n  产出: {t.result}\n")

    parts.append(f"\n## 失败/问题 (需要重新处理)\n{failed_info}\n")
    parts.append("\n请分析问题，只拆分需要修复的新任务。输出JSON格式。")

    return "\n".join(parts)
