from src.agents.adapters.real import RealACPAdapter


class ReasonixAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["npx", "reasonix", "--acp"]
