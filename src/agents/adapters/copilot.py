from src.agents.adapters.real import RealACPAdapter


class CopilotAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["copilot", "--acp"]
