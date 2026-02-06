from __future__ import annotations

import platform
import subprocess
from datetime import datetime

from malone.tools.base import BaseTool


class GetCurrentTimeTool(BaseTool):
    """Returns the current date and time."""

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Get the current date, time, and day of the week."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self) -> str:
        now = datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")


class GetSystemInfoTool(BaseTool):
    """Returns system information about the machine Malone is running on."""

    @property
    def name(self) -> str:
        return "get_system_info"

    @property
    def description(self) -> str:
        return "Get system information: OS, CPU, RAM, GPU, and disk usage."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self) -> str:
        info = []
        info.append(f"OS: {platform.system()} {platform.release()}")
        info.append(f"Machine: {platform.machine()}")

        try:
            import psutil
            mem = psutil.virtual_memory()
            info.append(f"RAM: {mem.total // (1024**3)}GB total, {mem.available // (1024**3)}GB available")
        except ImportError:
            pass

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                info.append(f"GPU: {result.stdout.strip()}")
        except Exception:
            pass

        return "\n".join(info)


class RunShellCommandTool(BaseTool):
    """Runs a shell command and returns the output."""

    @property
    def name(self) -> str:
        return "run_shell_command"

    @property
    def description(self) -> str:
        return (
            "Run a shell command on the local system and return its output. "
            "Use for checking system status, running scripts, managing services, etc."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
