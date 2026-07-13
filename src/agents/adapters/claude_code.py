from src.agents.adapters.real import RealACPAdapter


class ClaudeCodeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["claude-agent-acp"]
