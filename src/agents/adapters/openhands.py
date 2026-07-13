from src.agents.adapters.real import RealACPAdapter


class OpenHandsAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["openhands", "acp"]
