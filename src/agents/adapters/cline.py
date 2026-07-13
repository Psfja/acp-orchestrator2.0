from src.agents.adapters.real import RealACPAdapter


class ClineAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["cline", "acp"]
