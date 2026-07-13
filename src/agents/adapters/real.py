"""真实 ACP 适配器 — 通过 subprocess 启动 Agent 并通过 stdin/stdout JSON-RPC 2.0 通信。"""

import asyncio
import json
from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


class RealACPAdapter(ACPAdapter):
    """真实 ACP Agent 适配器基类。子类只需覆盖 get_launch_command()。"""

    def get_launch_command(self) -> list[str]:
        raise NotImplementedError

    async def spawn(self):
        cmd = self.get_launch_command()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc.stdin, proc.stdout

    async def initialize(self, writer, reader, session_config: dict) -> str:
        # Step 1: initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.11.0",
                "clientInfo": {"name": "acp-orchestrator", "version": "0.1.0"},
                "capabilities": {"fs": {}, "terminal": {}},
            },
        }
        await self._send_json(writer, init_msg)
        resp = await self._read_json(reader)

        # Step 2: session/new
        session_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {
                "cwd": ".",
                "systemPrompt": session_config.get("systemPrompt", ""),
            },
        }
        await self._send_json(writer, session_msg)
        resp = await self._read_json(reader)
        return resp.get("result", {}).get("sessionId", "unknown")

    async def send_prompt(self, writer, session_id: str, prompt: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": prompt}],
            },
        }
        await self._send_json(writer, msg)

    async def read_updates(self, reader) -> AsyncIterator[dict]:
        while True:
            try:
                line = await asyncio.wait_for(reader.readline(), timeout=300)
                if not line:
                    break
                msg = json.loads(line.decode("utf-8").strip())
                if "result" in msg and "id" in msg:
                    result = msg.get("result", {})
                    yield {"type": "result", "content": result.get("message", {}).get("text", str(result))}
                    break
                elif msg.get("method") == "session/update":
                    update = msg.get("params", {}).get("update", {})
                    yield update
            except asyncio.TimeoutError:
                yield {"type": "error", "content": "读取超时"}
                break

    async def close_session(self, writer, session_id: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/close",
            "params": {"sessionId": session_id},
        }
        try:
            await self._send_json(writer, msg)
        except Exception:
            pass

    async def _send_json(self, writer, data: dict) -> None:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        writer.write(line.encode("utf-8"))
        await writer.drain()

    async def _read_json(self, reader) -> dict:
        line = await reader.readline()
        if not line:
            raise EOFError("Agent 子进程意外退出")
        return json.loads(line.decode("utf-8").strip())
