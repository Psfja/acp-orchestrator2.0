from src.agents.adapters.real import RealACPAdapter


class OpenCodeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["opencode", "acp"]
