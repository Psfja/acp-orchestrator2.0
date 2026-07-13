"""验证所有 17 个 Agent 适配器的启动命令。"""
import pytest
from src.agents.adapters.claude_code import ClaudeCodeAdapter
from src.agents.adapters.codex import CodexAdapter
from src.agents.adapters.gemini import GeminiAdapter
from src.agents.adapters.copilot import CopilotAdapter
from src.agents.adapters.goose import GooseAdapter
from src.agents.adapters.cline import ClineAdapter
from src.agents.adapters.auggie import AuggieAdapter
from src.agents.adapters.kiro import KiroAdapter
from src.agents.adapters.opencode import OpenCodeAdapter
from src.agents.adapters.qwen_code import QwenCodeAdapter
from src.agents.adapters.vibe import VibeAdapter
from src.agents.adapters.droid import DroidAdapter
from src.agents.adapters.qoder import QoderAdapter
from src.agents.adapters.hermes import HermesAdapter
from src.agents.adapters.pi import PiAdapter
from src.agents.adapters.reasonix import ReasonixAdapter
from src.agents.adapters.openhands import OpenHandsAdapter


@pytest.mark.parametrize("adapter_cls, expected_cmd", [
    (ClaudeCodeAdapter, ["claude-code-acp"]),
    (CodexAdapter, ["npx", "@zed-industries/codex-acp"]),
    (GeminiAdapter, ["gemini", "--acp"]),
    (CopilotAdapter, ["copilot", "--acp"]),
    (GooseAdapter, ["goose", "acp"]),
    (ClineAdapter, ["cline", "acp"]),
    (AuggieAdapter, ["auggie", "acp"]),
    (KiroAdapter, ["kiro-cli", "acp"]),
    (OpenCodeAdapter, ["opencode", "acp"]),
    (QwenCodeAdapter, ["qwen-code", "acp"]),
    (VibeAdapter, ["vibe-acp"]),
    (DroidAdapter, ["droid", "acp"]),
    (QoderAdapter, ["npx", "@qoder-ai/qodercli", "--acp"]),
    (HermesAdapter, ["hermes", "acp"]),
    (PiAdapter, ["pi-acp"]),
    (ReasonixAdapter, ["npx", "reasonix", "--acp"]),
    (OpenHandsAdapter, ["openhands", "acp"]),
])
def test_adapter_launch_command(adapter_cls, expected_cmd):
    adapter = adapter_cls()
    assert adapter.get_launch_command() == expected_cmd


def test_all_adapters_inherit_from_real():
    from src.agents.adapters.real import RealACPAdapter
    adapters = [
        ClaudeCodeAdapter, CodexAdapter, GeminiAdapter, CopilotAdapter,
        GooseAdapter, ClineAdapter, AuggieAdapter, KiroAdapter,
        OpenCodeAdapter, QwenCodeAdapter, VibeAdapter, DroidAdapter,
        QoderAdapter, HermesAdapter, PiAdapter, ReasonixAdapter, OpenHandsAdapter,
    ]
    for cls in adapters:
        assert issubclass(cls, RealACPAdapter), f"{cls.__name__} 未继承 RealACPAdapter"
