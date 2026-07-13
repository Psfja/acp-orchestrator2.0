from src.agents.adapters.real import RealACPAdapter


class CodexAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["npx", "@zed-industries/codex-acp"]
