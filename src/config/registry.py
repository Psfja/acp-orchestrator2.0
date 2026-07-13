"""统一的适配器注册表 — main.py / repl.py / plugin.py 共用。"""

from src.agents.manager import AgentManager
from src.agents.adapters.mock import MockAdapter
from src.agents.adapters.direct_llm import DirectLLMAdapter
from src.agents.adapters.claude_code import ClaudeCodeAdapter
from src.agents.adapters.codex import CodexAdapter
from src.agents.adapters.opencode import OpenCodeAdapter
from src.agents.adapters.reasonix import ReasonixAdapter
from src.agents.adapters.pi import PiAdapter


def register_all_adapters(manager: AgentManager, use_real: bool = True) -> None:
    """注册所有适配器到 AgentManager。

    use_real=True:  已安装的 Agent 用真实适配器，其余 Mock 兜底
    use_real=False: 全部用 MockAdapter（测试/无 Agent 环境）
    """
    manager.register_adapter("mock", MockAdapter)
    manager.register_adapter("echo", MockAdapter)
    manager.register_adapter("direct_llm", DirectLLMAdapter)

    if use_real:
        manager.register_adapter("claude_code", ClaudeCodeAdapter)
        manager.register_adapter("codex", CodexAdapter)
        manager.register_adapter("opencode", OpenCodeAdapter)
        manager.register_adapter("reasonix", ReasonixAdapter)
        manager.register_adapter("pi", PiAdapter)
    else:
        for key in ("claude_code", "codex", "opencode", "reasonix", "pi"):
            manager.register_adapter(key, MockAdapter)

    # 未安装的 Agent 始终用 MockAdapter
    for key in ("gemini", "copilot", "goose", "cline", "auggie", "kiro",
                "qwen_code", "vibe", "droid", "qoder", "hermes", "openhands"):
        manager.register_adapter(key, MockAdapter)
