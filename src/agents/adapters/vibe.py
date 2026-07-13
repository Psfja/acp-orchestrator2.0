from src.agents.adapters.real import RealACPAdapter


class VibeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["vibe-acp"]
