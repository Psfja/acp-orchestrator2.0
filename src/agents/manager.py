from typing import AsyncIterator
from src.agents.adapter import ACPAdapter
from src.agents.session import AgentSession
from src.config.loader import AgentConfig
from src.logger.logger import Logger


class AgentManager:

    def __init__(self, logger: Logger | None = None):
        self._adapters: dict[str, type[ACPAdapter]] = {}
        self._sessions: dict[str, AgentSession] = {}
        self.logger = logger

    def register_adapter(self, name: str, adapter_cls: type[ACPAdapter]) -> None:
        self._adapters[name] = adapter_cls

    async def spawn(self, agent_key: str, config: AgentConfig) -> AgentSession:
        adapter_cls = self._adapters.get(config.adapter)
        if adapter_cls is None:
            raise ValueError(f"未注册的适配器: {config.adapter}")

        adapter = adapter_cls()
        writer, reader = await adapter.spawn()

        sid = await adapter.initialize(writer, reader, {
            "cwd": ".",
            "systemPrompt": config.system_prompt,
        })

        session = AgentSession(
            agent_key=agent_key,
            config=config,
            adapter=adapter,
            writer=writer,
            reader=reader,
            session_id=sid,
        )
        session.mark_active()
        self._sessions[agent_key] = session

        if self.logger:
            self.logger.log_router(f"Agent启动: {config.name} (session: {sid})")

        return session

    async def send_task(self, session: AgentSession, prompt: str) -> AsyncIterator[dict]:
        await session.adapter.send_prompt(session.writer, session.session_id, prompt)
        async for update in session.adapter.read_updates(session.reader):
            yield update

    async def kill(self, session: AgentSession) -> None:
        await session.adapter.close_session(session.writer, session.session_id)
        if session.agent_key in self._sessions:
            del self._sessions[session.agent_key]
