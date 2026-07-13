from src.agents.adapters.real import RealACPAdapter


class GooseAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["goose", "acp"]
