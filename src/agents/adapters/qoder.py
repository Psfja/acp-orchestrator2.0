from src.agents.adapters.real import RealACPAdapter


class QoderAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["npx", "@qoder-ai/qodercli", "--acp"]
