from abc import ABC, abstractmethod
from typing import AsyncIterator


class ACPAdapter(ABC):

    @abstractmethod
    def get_launch_command(self) -> list[str]:
        ...

    @abstractmethod
    async def spawn(self):
        ...

    @abstractmethod
    async def initialize(self, writer, reader, session_config: dict) -> str:
        ...

    @abstractmethod
    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        ...

    @abstractmethod
    async def read_updates(self, reader) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def close_session(self, writer, session_id: str) -> None:
        ...
