"""真实 ACP 适配器 — 通过 subprocess 启动 Agent 并通过 stdin/stdout JSON-RPC 2.0 通信。"""

import asyncio
import json
import os
import shutil
from pathlib import Path
from src.agents.adapter import ACPAdapter
from typing import AsyncIterator


def _find_npm_binary(name: str) -> str | None:
    """在 npm 全局目录查找可执行文件。"""
    try:
        npm_root = os.popen("npm root -g").read().strip()
        npm_bin = Path(npm_root).parent
        for ext in ("", ".cmd", ".ps1", ".exe"):
            candidate = npm_bin / f"{name}{ext}"
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass
    return None


def _extract_text(content) -> str:
    """安全地从 ACP 消息中提取文本内容。支持 str、dict、list。"""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return content.get("text", "") or content.get("content", "") or _extract_text(list(content.values()))
    if isinstance(content, list):
        return " ".join(_extract_text(c) for c in content)
    return str(content) if content else ""


class RealACPAdapter(ACPAdapter):
    """真实 ACP Agent 适配器基类。子类只需覆盖 get_launch_command()。"""

    def get_launch_command(self) -> list[str]:
        raise NotImplementedError

    async def spawn(self):
        cmd = self.get_launch_command()
        resolved = shutil.which(cmd[0])
        if not resolved:
            resolved = _find_npm_binary(cmd[0])
        if not resolved:
            raise FileNotFoundError(f"找不到可执行文件: {cmd[0]}")

        full_cmd = [resolved] + cmd[1:]
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc.stdin, proc.stdout

    async def initialize(self, writer, reader, session_config: dict) -> str:
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "clientInfo": {"name": "acp-orchestrator", "version": "0.1.0"},
                "capabilities": {"fs": {}, "terminal": {}},
            },
        }
        await self._send_json(writer, init_msg)
        resp = await self._read_json(reader)

        session_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {
                "cwd": os.path.abspath("."),
                "mcpServers": [],
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
        timeout = getattr(self, "_timeout", 300)
        while True:
            try:
                line = await asyncio.wait_for(self._read_line(reader), timeout=timeout)
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if "result" in msg and "id" in msg:
                    result = msg.get("result", {})
                    text = _extract_text(result.get("message", {}))
                    yield {"type": "result", "content": text or str(result)}
                    break
                elif msg.get("method") == "session/update":
                    update = msg.get("params", {}).get("update", {})
                    update_type = update.get("type", "")
                    if update_type in ("thinking", "reasoning"):
                        continue
                    content = update.get("content", "")
                    update["content"] = _extract_text(content)
                    yield update
            except asyncio.TimeoutError:
                yield {"type": "error", "content": "读取超时"}
                break

    async def _read_line(self, reader) -> str:
        """读取一行 JSON，自动处理超大消息（>64KB）。"""
        line = await reader.readline()
        if not line:
            return ""
        text = line.decode("utf-8").strip()
        # 尝试解析，成功则返回
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # 可能是超大消息被截断，继续读取直到能解析
            buffer = text
            for _ in range(20):
                chunk = await asyncio.wait_for(reader.readline(), timeout=5)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8").strip()
                try:
                    json.loads(buffer)
                    return buffer
                except json.JSONDecodeError:
                    continue
            return buffer

    async def close_session(self, writer, session_id: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/close",
            "params": {"sessionId": session_id},
        }
        try:
            await self._send_json(writer, msg)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    async def _send_json(self, writer, data: dict) -> None:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        writer.write(line.encode("utf-8"))
        await writer.drain()

    async def _read_json(self, reader) -> dict:
        text = await self._read_line(reader)
        if not text:
            raise EOFError("Agent 子进程意外退出")
        return json.loads(text)
