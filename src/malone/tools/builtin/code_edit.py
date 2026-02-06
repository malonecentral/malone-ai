from __future__ import annotations

import os
import subprocess

from malone.tools.base import BaseTool

PROJECT_DIR = "/mnt/c/Users/denni/malone-ai"


class ClaudeCodeTool(BaseTool):
    """Spawns Claude Code CLI to edit Malone's own source code."""

    @property
    def name(self) -> str:
        return "claude_code"

    @property
    def description(self) -> str:
        return (
            "Spawn a Claude Code CLI session to edit Malone's own source code. "
            "Use this for complex code changes: adding features, fixing bugs, "
            "refactoring, or improving Malone itself. Claude Code can read, "
            "write, and edit files in the project. A git commit is created "
            "before changes as a safety net."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "A detailed description of what code changes to make. "
                        "Be specific about what to add, modify, or fix. "
                        "Example: 'Add a weather tool that fetches weather from OpenWeatherMap API'"
                    ),
                },
            },
            "required": ["task"],
        }

    async def execute(self, task: str) -> str:
        # Safety: commit current state before making changes
        safety_result = subprocess.run(
            ["git", "stash", "--include-untracked", "-m", "malone-auto-save"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
        )

        try:
            # Run Claude Code with the task
            env = os.environ.copy()
            result = subprocess.run(
                [
                    "claude",
                    "--print",
                    "--dangerously-skip-permissions",
                    task,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=PROJECT_DIR,
                env=env,
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"

            # Check what changed
            diff_result = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

            if diff_result.stdout.strip():
                # Auto-commit the changes
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=PROJECT_DIR,
                )
                subprocess.run(
                    [
                        "git", "commit", "-m",
                        f"Malone self-edit: {task[:80]}",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_DIR,
                )
                output += f"\n\nFiles changed:\n{diff_result.stdout}"
            else:
                output += "\n\nNo files were modified."

            return output.strip() or "(no output from Claude Code)"

        except subprocess.TimeoutExpired:
            return "Error: Claude Code session timed out after 5 minutes"
        finally:
            # Restore stashed changes if any were stashed
            if "Saved working directory" in (safety_result.stdout or ""):
                subprocess.run(
                    ["git", "stash", "pop"],
                    capture_output=True,
                    cwd=PROJECT_DIR,
                )
