from src.agents.adapters.real import RealACPAdapter


class HermesAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["hermes", "acp"]
