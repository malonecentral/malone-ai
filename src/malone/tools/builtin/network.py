from __future__ import annotations

import asyncio
import shlex

from malone.tools.base import BaseTool


class SSHCommandTool(BaseTool):
    """Execute commands on remote hosts via SSH."""

    @property
    def name(self) -> str:
        return "ssh_command"

    @property
    def description(self) -> str:
        return (
            "Run a command on a remote host via SSH. Requires SSH key-based "
            "authentication to be configured (no password prompts). "
            "Use for managing routers, switches, servers, and other network devices."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Hostname or IP address to connect to (e.g. 'router.local' or '192.168.1.1')",
                },
                "command": {
                    "type": "string",
                    "description": "The command to execute on the remote host",
                },
                "user": {
                    "type": "string",
                    "description": "SSH username (defaults to current user if not specified)",
                },
                "port": {
                    "type": "integer",
                    "description": "SSH port (defaults to 22)",
                },
            },
            "required": ["host", "command"],
        }

    async def execute(
        self, host: str, command: str, user: str = "", port: int = 22
    ) -> str:
        ssh_args = [
            "ssh",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-p", str(port),
        ]
        if user:
            ssh_args.extend(["-l", user])
        ssh_args.append(host)
        ssh_args.append(command)

        try:
            proc = await asyncio.create_subprocess_exec(
                *ssh_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )

            output = stdout.decode(errors="replace")
            if stderr:
                output += f"\nSTDERR: {stderr.decode(errors='replace')}"
            if proc.returncode != 0:
                output += f"\nExit code: {proc.returncode}"
            return output.strip() or "(no output)"

        except asyncio.TimeoutError:
            proc.kill()
            return f"Error: SSH command timed out after 30 seconds"
        except FileNotFoundError:
            return "Error: ssh command not found"


class KubectlTool(BaseTool):
    """Execute kubectl commands for Kubernetes cluster management."""

    @property
    def name(self) -> str:
        return "kubectl"

    @property
    def description(self) -> str:
        return (
            "Run kubectl commands to manage the Kubernetes cluster. "
            "Can list pods, services, deployments, check logs, scale resources, etc. "
            "Examples: 'get pods -A', 'logs deploy/myapp', 'get nodes'."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "kubectl arguments (e.g. 'get pods -n default', 'logs deploy/myapp --tail=50')",
                },
                "context": {
                    "type": "string",
                    "description": "Kubernetes context to use (optional, uses current context if not specified)",
                },
            },
            "required": ["args"],
        }

    async def execute(self, args: str, context: str = "") -> str:
        cmd = ["kubectl"]
        if context:
            cmd.extend(["--context", context])
        cmd.extend(shlex.split(args))

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )

            output = stdout.decode(errors="replace")
            if stderr:
                output += f"\nSTDERR: {stderr.decode(errors='replace')}"
            if proc.returncode != 0:
                output += f"\nExit code: {proc.returncode}"
            return output.strip() or "(no output)"

        except asyncio.TimeoutError:
            proc.kill()
            return "Error: kubectl command timed out after 30 seconds"
        except FileNotFoundError:
            return "Error: kubectl not found. Is it installed?"
