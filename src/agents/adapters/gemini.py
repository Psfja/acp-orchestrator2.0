from src.agents.adapters.real import RealACPAdapter


class GeminiAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["gemini", "--acp"]
