from src.agents.adapters.real import RealACPAdapter


class QwenCodeAdapter(RealACPAdapter):
    def get_launch_command(self) -> list[str]:
        return ["qwen-code", "acp"]
