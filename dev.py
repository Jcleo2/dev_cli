import os
import sys
import time
import subprocess
import platform
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from toolbox import json_tool, base64
import ai
import agent


# ─────────────────────────────────────────────
# Paths / config
# ─────────────────────────────────────────────

CONFIG_DIR = Path.home() / ".dev"
CONFIG_FILE = CONFIG_DIR / "config"
PROJECTS_FILE = CONFIG_DIR / "projects"


# ─────────────────────────────────────────────
# ANSI
# ─────────────────────────────────────────────

RESET = "\033[0m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

HISTORY_FILE = Path.home() / ".dev" / "history"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

session = PromptSession(
        history =FileHistory(str(HISTORY_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
)
# ─────────────────────────────────────────────
# Logo
# ─────────────────────────────────────────────

LOGO = [
    "██████╗ ███████╗██╗   ██╗",
    "██╔══██╗██╔════╝██║   ██║",
    "██║  ██║█████╗  ██║   ██║",
    "██║  ██║██╔══╝  ╚██╗ ██╔╝",
    "██████╔╝███████╗ ╚████╔╝ ",
    "╚═════╝ ╚══════╝  ╚═══╝  ",
    ]


# ─────────────────────────────────────────────
# Terminal helpers
# ─────────────────────────────────────────────

def clear_screen():
    os.system("clear")


def type_text(text, delay=0.015):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def status():
    print(
        f"{DIM}"
        f"Project: {Path.cwd()}"
        f"{RESET}"
    )

    print(
        f"{DIM}"
        f"Model: {ai.MODEL}"
        f"{RESET}"
        )

    print()


# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

def load_config():
    config = {}

    if not CONFIG_FILE.exists():
        return config

    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                line = line.strip()

                if not line or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                config[key] = value

    except Exception:
        pass

    return config


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


def get_speed():
    config = load_config()
    return config.get("speed", "powerful")


# ─────────────────────────────────────────────
# Recent projects
# ─────────────────────────────────────────────

def load_projects():
    if not PROJECTS_FILE.exists():
        return []

    projects = []

    try:
        with open(PROJECTS_FILE, "r") as f:
            for line in f:
                path = line.strip()

                if not path:
                    continue

                path = os.path.expanduser(path)

                if os.path.isdir(path):
                    projects.append(str(Path(path).resolve()))

    except Exception:
        pass

    return projects


def save_projects(projects):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Remove duplicates while preserving order
    unique = []

    for project in projects:
        project = str(Path(project).expanduser().resolve())

        if project not in unique:
            unique.append(project)

    with open(PROJECTS_FILE, "w") as f:
        for project in unique[:20]:
            f.write(project + "\n")


def remember_project(path):
    path = str(Path(path).expanduser().resolve())

    projects = load_projects()

    if path in projects:
        projects.remove(path)

    projects.insert(0, path)

    save_projects(projects)


# ─────────────────────────────────────────────
# Project switcher
# ─────────────────────────────────────────────

def switch_project():

    while True:
        clear_screen()

        current = Path.cwd().resolve()
        projects = load_projects()

        # Always make current project the first entry
        current_string = str(current)

        if current_string in projects:
            projects.remove(current_string)

        projects.insert(0, current_string)

        print()
        print(f"{CYAN}{BOLD}DEV • PROJECTS{RESET}")
        print("────────────────────────────────────────")
        print()

        print(
            f"{DIM}Current:{RESET} "
            f"{GREEN}{current}{RESET}"
        )

        print()

        for index, project in enumerate(projects[:10], start=1):
            project_path = Path(project)

            if project_path == current:
                marker = f"{GREEN}●{RESET}"
            else:
                marker = " "

            print(
                f"  {marker} "
                f"{CYAN}{index}{RESET}. "
                f"{project_path.name}"
            )

            print(
                f"      {DIM}{project_path}{RESET}"
            )

        print()

        next_number = min(len(projects), 10) + 1

        print(
            f"  {CYAN}N{RESET}. "
            "Open another folder"
        )

        print(
            f"  {CYAN}B{RESET}. "
            "Go back"
        )

        print()

        choice = input("Select > ").strip()

        if choice.lower() == "b":
            return

        if choice.lower() == "n":
            print()

            raw_path = input(
                "Folder path > "
            ).strip()

            if not raw_path:
                continue

            raw_path = os.path.expanduser(raw_path)

            if not os.path.isabs(raw_path):
                raw_path = os.path.abspath(raw_path)

            path = Path(raw_path).resolve()

            if not path.exists():
                print()
                print(
                    f"{RED}"
                    "That folder does not exist."
                    f"{RESET}"
                )
                input("\nPress Enter to continue...")
                continue

            if not path.is_dir():
                print()
                print(
                    f"{RED}"
                    "That path is not a folder."
                    f"{RESET}"
                )
                input("\nPress Enter to continue...")
                continue

            os.chdir(path)

            # Update the agent's project root
            agent.PROJECT_ROOT = Path.cwd().resolve()

            remember_project(path)

            print()
            print(
                f"{GREEN}"
                f"Switched to {path}"
                f"{RESET}"
            )

            input("\nPress Enter to continue...")
            return

        try:
            number = int(choice)
        except ValueError:
            continue

        if number < 1 or number > min(len(projects), 10):
            continue

        selected = Path(projects[number - 1]).resolve()

        if not selected.is_dir():
            continue

        os.chdir(selected)

        # IMPORTANT:
        # The agent normally locks itself to the directory
        # where it was started. Update that when switching.
        agent.PROJECT_ROOT = Path.cwd().resolve()

        remember_project(selected)

        print()
        print(
            f"{GREEN}"
            f"Switched to {selected}"
            f"{RESET}"
        )

        time.sleep(0.5)

        return


# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────

def banner(animated=True):
    clear_screen()

    print()

    if animated:
        time.sleep(1)

        for line in LOGO:
            print(
                f"{CYAN}{line}{RESET}"
            )
            time.sleep(0.08)

    else:
        for line in LOGO:
            print(
                f"{CYAN}{line}{RESET}"
            )

    print()
    print(
        f"{BOLD}"
        "AI-powered terminal development."
        f"{RESET}"
    )

    print()


# ─────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────

def show_help():
    print()
    print(f"{CYAN}{BOLD}DEV COMMANDS{RESET}")
    print("────────────────────────────────────────")
    print()

    print(
        f"  {CYAN}ask <prompt>{RESET}"
        "       Ask the AI"
    )

    print(
        f"  {CYAN}agent <task>{RESET}"
        "       Run the coding agent"
    )

    print(
        f"  {CYAN}project{RESET}"
        "              Switch projects"
    )

    print(
        f"  {CYAN}config{RESET}"
        "               Open preferences"
    )

    print(
        f"  {CYAN}model{RESET}"
        "                Show current model"
    )

    print(
        f"  {CYAN}doctor{RESET}"
        "              Check DEV"
    )

    print(
        f"  {CYAN}shell{RESET}"
        "               Open your normal shell"
    )

    print(
        f"  {CYAN}clear{RESET}"
        "               Clear the terminal"
    )

    print(
        f"  {CYAN}help{RESET}"
        "                Show this menu"
    )

    print(
        f"  {CYAN}exit{RESET}"
        "                Quit DEV"
    )

    print()

    print(
        f"{DIM}"
        "Any command DEV doesn't recognize is passed to zsh."
        f"{RESET}"
    )

    print()


# ─────────────────────────────────────────────
# AI
# ─────────────────────────────────────────────

def ask_ai(prompt):
    if not prompt.strip():
        print(
            f"{YELLOW}"
            "Usage: ask <question>"
            f"{RESET}"
        )
        return

    print()
    print(f"{CYAN}DEV • AI{RESET}")
    print("────────────────────────────────────────")
    print()

    try:
        response = ai.ask_ai(prompt)
        print(response)

    except KeyboardInterrupt:
        print()
        print(
            f"{YELLOW}"
            "AI interrupted."
            f"{RESET}"
        )

    except Exception as e:
        print(
            f"{RED}"
            "AI error:"
            f"{RESET} {e}"
        )

    print()


# ─────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────

def run_agent(prompt):
    if not prompt.strip():
        print(
            f"{YELLOW}"
            "Usage: agent <task>"
            f"{RESET}"
        )
        return

    print()
    print(f"{CYAN}DEV • AGENT{RESET}")
    print("────────────────────────────────────────")
    print()

    try:
        agent.agent(prompt)

    except KeyboardInterrupt:
        print()
        print(
            f"{YELLOW}"
            "Agent interrupted."
            f"{RESET}"
        )

    except Exception as e:
        print(
            f"{RED}"
            "Agent error:"
            f"{RESET} {e}"
        )

    print()


# ─────────────────────────────────────────────
# Preferences
# ─────────────────────────────────────────────

def config_menu():
    config_path = Path(__file__).parent / "config.py"

    if not config_path.exists():
        print(
            f"{RED}"
            "config.py was not found."
            f"{RESET}"
        )
        return

    try:
        subprocess.run(
            [
                sys.executable,
                str(config_path),
            ],
            cwd=Path(__file__).parent,
        )

    except Exception as e:
        print(
            f"{RED}"
            "Could not open preferences:"
            f"{RESET} {e}"
        )


# ─────────────────────────────────────────────
# Doctor
# ─────────────────────────────────────────────

def doctor():
    print()
    print(f"{CYAN}{BOLD}DEV • DOCTOR{RESET}")
    print("────────────────────────────────────────")
    print()

    checks = []

    checks.append(
        (
            "Python",
            sys.version.split()[0],
            True,
        )
    )

    checks.append(
        (
            "Platform",
            f"{platform.system()} {platform.machine()}",
            True,
        )
    )

    checks.append(
        (
            "Project",
            str(Path.cwd()),
            True,
        )
    )

    checks.append(
        (
            "Model",
            ai.MODEL,
            True,
        )
    )

    checks.append(
        (
            "Ollama",
            "Available",
            True,
        )
    )

    checks.append(
        (
            "Agent",
            "Available",
            True,
        )
    )

    for name, value, good in checks:
        if good:
            symbol = f"{GREEN}✓{RESET}"
        else:
            symbol = f"{RED}✗{RESET}"

        print(
            f"  {symbol} "
            f"{name:<12} "
            f"{DIM}{value}{RESET}"
        )

    print()


# ─────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────

def show_model():
    print()
    print(
        f"{CYAN}DEV • MODEL{RESET}"
    )
    print("────────────────────────────────────────")
    print()

    print(
        f"Model: "
        f"{GREEN}{ai.MODEL}{RESET}"
    )

    print(
        f"Speed: "
        f"{GREEN}{get_speed()}{RESET}"
    )

    print()


# ─────────────────────────────────────────────
# Shell
# ─────────────────────────────────────────────

def run_shell(command):
    shell = os.environ.get(
        "SHELL",
        "/bin/zsh",
    )

    try:
        subprocess.run(
            command,
            shell=True,
            executable=shell,
            cwd=os.getcwd(),
        )

    except KeyboardInterrupt:
        print()


def launch_real_shell():
    shell = os.environ.get(
        "SHELL",
        "/bin/zsh",
    )

    print()
    print(
        f"{CYAN}DEV • NATIVE SHELL{RESET}"
    )

    print(
        f"{DIM}"
        "Powerlevel10k, aliases, autocomplete, etc. preserved."
        f"{RESET}"
    )

    print()

    try:
        subprocess.run(
            [shell, "-l"],
            cwd=os.getcwd(),
        )

    except KeyboardInterrupt:
        print()

    print()


# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────

def startup():
    banner(animated=True)

    remember_project(Path.cwd())

    status()

    print(
        f"{DIM}"
        "Type 'help' for commands."
        f"{RESET}"
    )

    print()


# ─────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────

def main():
    startup()

    while True:
        try:
            command = session.prompt(
                ANSI(f"{CYAN}DEV > {RESET}")
            ).strip()

        except KeyboardInterrupt:
            print()
            continue

        except EOFError:
            print()
            break

        if not command:
            continue

        if command == "exit":
            print()
            print(
                f"{DIM}"
                "Leaving DEV."
                f"{RESET}"
            )
            print()
            break

        elif command == "help":
            show_help()

        elif command == "clear":
            banner(animated=False)
            status()

        elif command == "config":
            config_menu()
            print()
            status()

        elif command == "model":
            show_model()

        elif command.startswith("json "):
            json_tool.run(command[5:].split())

        elif command == "json":
            json_tool.run([])

        elif command.startswith("base64 "):
            base64.run(command[7:].split())

        elif command == "base64":
            base64.run([])

        elif command == "doctor":
            doctor()

        elif command == "project":
            switch_project()
            print()
            status()

        elif command == "shell":
            launch_real_shell()
            status()

        elif command.startswith("project "):
            target = command[8:].strip()

            if target:
                target = os.path.expanduser(target)

                if not os.path.isabs(target):
                    target = os.path.abspath(target)

                path = Path(target).resolve()

                if path.is_dir():
                    os.chdir(path)
                    agent.PROJECT_ROOT = Path.cwd().resolve()
                    remember_project(path)

                    print()
                    print(
                        f"{GREEN}"
                        f"Switched to {path}"
                        f"{RESET}"
                    )
                    print()

                else:
                    print()
                    print(
                        f"{RED}"
                        "Project folder not found."
                        f"{RESET}"
                    )
                    print()

        elif command.startswith("agent "):
            run_agent(command[6:])

        elif command == "agent":
            print(
                f"{YELLOW}"
                "Usage: agent <task>"
                f"{RESET}"
            )

        elif command.startswith("ask "):
            ask_ai(command[4:])

        elif command == "ask":
            print(
                f"{YELLOW}"
                "Usage: ask <question>"
                f"{RESET}"
            )

        else:
            run_shell(command)


if __name__ == "__main__":
    main()

