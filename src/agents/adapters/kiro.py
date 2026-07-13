from src.agents.adapters.real import RealACPAdapter


class KiroAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["kiro-cli", "acp"]
