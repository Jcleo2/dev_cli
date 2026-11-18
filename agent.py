import os
import json
import re
import subprocess
import difflib
from pathlib import Path

import ai


# ─────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────

PROJECT_ROOT = Path.cwd().resolve()


def safe_path(path):
    target = (PROJECT_ROOT / path).resolve()

    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError:
        return None

    return target


# ─────────────────────────────────────────────
# File tools
# ─────────────────────────────────────────────

def read_file(path):
    target = safe_path(path)

    if target is None:
        return "ERROR: Access outside the project directory is not allowed."

    if not target.exists():
        return f"ERROR: File does not exist: {path}"

    if not target.is_file():
        return f"ERROR: Not a file: {path}"

    try:
        return target.read_text()
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def list_files(path="."):
    target = safe_path(path)

    if target is None:
        return "ERROR: Access outside the project directory is not allowed."

    if not target.exists():
        return f"ERROR: Directory does not exist: {path}"

    if not target.is_dir():
        return f"ERROR: Not a directory: {path}"

    ignored = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".next",
        "dist",
        "build",
    }

    files = []

    for item in sorted(target.rglob("*")):
        try:
            relative = item.relative_to(PROJECT_ROOT)
        except ValueError:
            continue

        if any(part in ignored for part in relative.parts):
            continue

        if item.is_file():
            files.append(str(relative))

    if not files:
        return "Project contains no visible files."

    return "\n".join(files[:500])


def search_files(query):
    query = query.strip()

    if not query:
        return "ERROR: Search query cannot be empty."

    ignored = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".next",
        "dist",
        "build",
    }

    results = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        try:
            relative = path.relative_to(PROJECT_ROOT)
        except ValueError:
            continue

        if any(part in ignored for part in relative.parts):
            continue

        try:
            text = path.read_text()
        except Exception:
            continue

        if query.lower() in text.lower():
            results.append(str(relative))

        if len(results) >= 100:
            break

    if not results:
        return f"No files found containing: {query}"

    return "\n".join(results)


# ─────────────────────────────────────────────
# Diff / write
# ─────────────────────────────────────────────

def show_diff(path, old_content, new_content):
    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile=path,
        tofile=path,
        lineterm="",
    )

    lines = list(diff)

    if not lines:
        return False

    print()
    print("DEV • PROPOSED CHANGE")
    print("────────────────────────────────────────")
    print()

    for line in lines:
        if line.startswith("+++"):
            print(f"\033[32m{line}\033[0m")
        elif line.startswith("---"):
            print(f"\033[31m{line}\033[0m")
        elif line.startswith("@@"):
            print(f"\033[36m{line}\033[0m")
        elif line.startswith("+"):
            print(f"\033[32m{line}\033[0m")
        elif line.startswith("-"):
            print(f"\033[31m{line}\033[0m")
        else:
            print(line)

    print()
    return True


def write_file(path, content):
    target = safe_path(path)

    if target is None:
        return "ERROR: Access outside the project directory is not allowed."

    old_content = ""

    if target.exists():
        if not target.is_file():
            return f"ERROR: Not a file: {path}"

        try:
            old_content = target.read_text()
        except Exception as e:
            return f"ERROR reading existing file: {e}"

    show_diff(path, old_content, content)

    if target.exists():
        print(f"DEV • AGENT wants to modify: {path}")
    else:
        print(f"DEV • AGENT wants to create: {path}")

    print()

    answer = input("Apply this change? [y/N] ").strip().lower()

    if answer != "y":
        return "WRITE CANCELLED BY USER."

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"Successfully wrote {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


# ─────────────────────────────────────────────
# Command tool
# ─────────────────────────────────────────────

def run_command(command):
    print()
    print("DEV • AGENT wants to run:")
    print()
    print(f"  {command}")
    print()

    answer = input("Run this command? [y/N] ").strip().lower()

    if answer != "y":
        return "COMMAND CANCELLED BY USER."

    try:
        shell = os.environ.get("SHELL", "/bin/zsh")

        result = subprocess.run(
            command,
            shell=True,
            executable=shell,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        if len(output) > 12000:
            output = output[-12000:]

        return (
            f"Exit code: {result.returncode}\n"
            f"Output:\n{output}"
        )

    except Exception as e:
        return f"ERROR running command: {e}"


# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file inside the current project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the current project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search project files for text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or replace a text file. Always inspect existing files first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "content": {
                        "type": "string",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command inside the current project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    },
                },
                "required": ["command"],
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
    "search_files": search_files,
    "write_file": write_file,
    "run_command": run_command,
}


# ─────────────────────────────────────────────
# Tool-call parsing
# ─────────────────────────────────────────────

def parse_text_tool_calls(text):
    """
    Handles models that return tool calls as JSON inside message content.

    Example:

    [
      {
        "name": "write_file",
        "arguments": {
          "path": "hello.py",
          "content": "print('hello world')"
        }
      }
    ]
    """

    if not text:
        return []

    text = text.strip()

    candidates = [text]

    # Handle markdown code fences
    fenced = re.findall(
        r"```(?:json)?\s*(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    candidates.extend(fenced)

    for candidate in candidates:
        candidate = candidate.strip()

        try:
            data = json.loads(candidate)
        except Exception:
            continue

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            continue

        calls = []

        for item in data:
            if not isinstance(item, dict):
                continue

            name = item.get("name")

            if not name:
                function = item.get("function", {})
                name = function.get("name")

            arguments = item.get("arguments", {})

            if not arguments:
                function = item.get("function", {})
                arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    continue

            if name and isinstance(arguments, dict):
                calls.append(
                    {
                        "name": name,
                        "arguments": arguments,
                    }
                )

        if calls:
            return calls

    return []


# ─────────────────────────────────────────────
# Agent prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are DEV Agent, an autonomous coding agent.

You are operating inside the user's current project directory.

Available tools:

- list_files(path)
- search_files(query)
- read_file(path)
- write_file(path, content)
- run_command(command)

Rules:

1. Understand the project before changing it.
2. Use tools instead of merely describing what you would do.
3. Read relevant files before modifying them.
4. Never modify files outside the current project.
5. Make the smallest reasonable changes.
6. After making changes, run appropriate tests when useful.
7. Never claim a change was made unless write_file succeeded.
8. Never claim a command succeeded unless its result shows success.
9. The user must approve every file modification.
10. The user must approve every shell command.
11. If the task is simple, do not overcomplicate it.
12. Finish the user's requested task.
13. If you need to create a file, actually use write_file.
14. If you need to test something, actually use run_command.
15. Do not output fake tool calls as ordinary text.
16. When tools are available, use them.
"""


# ─────────────────────────────────────────────
# Execute tool
# ─────────────────────────────────────────────

def execute_tool(name, arguments):
    tool = TOOL_FUNCTIONS.get(name)

    if tool is None:
        return f"ERROR: Unknown tool {name}"

    print()
    print(
        f"DEV • AGENT → {name}"
    )

    try:
        return tool(**arguments)
    except Exception as e:
        return f"ERROR executing tool: {e}"


# ─────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────

def agent(prompt):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    max_steps = 20

    for _ in range(max_steps):

        response = ai.agent_chat(messages, TOOLS)

        message = response["message"]

        native_tool_calls = message.get(
            "tool_calls",
            [],
        )

        text = message.get(
            "content",
            "",
        )

        parsed_text_calls = parse_text_tool_calls(text)

        # ─────────────────────────────────────
        # Native Ollama tool calls
        # ─────────────────────────────────────

        if native_tool_calls:

            messages.append(message)

            for tool_call in native_tool_calls:
                function = tool_call["function"]

                name = function["name"]
                arguments = function.get(
                    "arguments",
                    {},
                )

                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                result = execute_tool(
                    name,
                    arguments,
                )

                tool_result = {
                    "role": "tool",
                    "content": str(result),
                }
                if tool_call.get("id"):
                    tool_result["tool_call_id"] = tool_call["id"]
                messages.append(tool_result)

            continue

        # ─────────────────────────────────────
        # Text-based tool calls
        # ─────────────────────────────────────

        if parsed_text_calls:

            # Do not display raw JSON to the user.
            messages.append(
                {
                    "role": "assistant",
                    "content": text,
                }
            )

            for call in parsed_text_calls:
                result = execute_tool(
                    call["name"],
                    call["arguments"],
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Tool result for "
                            f"{call['name']}:\n"
                            f"{result}"
                        ),
                    }
                )

            continue

        # ─────────────────────────────────────
        # Normal response
        # ─────────────────────────────────────

        if text:
            print()
            print(text)

        break

    else:
        print()
        print(
            "\033[33m"
            "Agent stopped after reaching its step limit."
            "\033[0m"
        )


# ─────────────────────────────────────────────
# Standalone mode
# ─────────────────────────────────────────────

def main():
    print()
    print("DEV • AGENT")
    print("────────────────────────────────────────")
    print(f"Model: {ai.MODEL}")
    print(f"Project: {PROJECT_ROOT}")
    print()

    prompt = input(
        "What should I work on?\n\n"
        "DEV/agent > "
    )

    if not prompt.strip():
        return

    agent(prompt)


if __name__ == "__main__":
    ai.ensure_model()
    main()
