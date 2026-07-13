from src.agents.adapters.real import RealACPAdapter


class DroidAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["droid", "acp"]
