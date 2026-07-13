from src.agents.adapters.real import RealACPAdapter


class AuggieAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["auggie", "acp"]
