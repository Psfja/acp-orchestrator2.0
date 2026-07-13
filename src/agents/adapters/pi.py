from src.agents.adapters.real import RealACPAdapter


class PiAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["pi-acp"]
