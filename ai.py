import ollama
from openai import OpenAI
import subprocess 
import platform
import os
import keyring
import getpass

CONFIG_DIR = os.path.expanduser("~/.dev")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config")

PROVIDER = "ollama"


def get_hardware():
    system = platform.system()
    machine = platform.machine()

    ram_gb = 0

    if system == "Darwin":
        try:
            ram_bytes = int(
                    subprocess.check_output(
                        ["sysctl", "-n", "hw.memsize"],
                        text=True
                    ).strip()
            )
            ram_gb = ram_bytes // (1024 ** 3)
        except Exception:
            pass

    return {
        "system": system, 
        "machine": machine, 
        "ram_gb": ram_gb
    }


def load_speed():
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if line.startswith("speed="):
                return line.strip().split("=", 1)[1]

    return None

def choose_model():
    saved = load_speed()

    if saved == "blazing":
        return "qwen3:4b"

    if saved == "faster":
        return "qwen3:8b"

    if saved == "powerful":
        ram = get_hardware()["ram_gb"]

        if ram >= 64:
            return "qwen3:30b"
        elif ram >= 32:
            return "qwen3:14b"
        else:
            return "qwen3:14b"

    print()
    print("How should DEV run?")
    print("1. BLAZING")
    print("2. FASTER")
    print("3. MOST POWERFUL")

    choice = input("Choose 1-3: ")

    if choice == "1":
        speed = "blazing"
        model = "qwen3:4b"
    elif choice == "2":
        speed = "faster"
        model = "qwen3:8b"
    else:
        speed = "powerful"

        ram = get_hardware()["ram_gb"]

        if ram >= 64:
            model = "qwen3:30b"
        elif ram >= 32:
            model = "qwen3:14b"
        else:
            model = "qwen3:14b"

    os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        f.write(f"speed={speed}\n")

    return model
   
MODEL = choose_model()

def ask_ollama(prompt: str) -> str:
    response = ollama.chat(
            model=MODEL, 
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        
    return response["message"]["content"]

def get_openai_key():
    return keyring.get_password("DEV", "openai_api_key")

def ask_openai(prompt: str, model:str) -> str:

    key = get_openai_key()

    if not key:
        raise ValueError("OpenAI API key is not configured.")

    client = OpenAI(api_key=key)

    response = client.responses.create(
            model=model,
            input=prompt,
    )

    return response.output_text

def get_ollama_models():
    models = ollama.list()
    return [m.model for m in models.models]

def get_openai_models():
    client = OpenAI()

    models = client.models.list()

    return [model.id for model in models.data]

def get_models():
    if PROVIDER == "ollama": 
        return get_ollama_models()

    if PROVIDER == "openai":
        return get_openai_models()

    raise ValueError(f"Unknown AI provider: {PROVIDER}")

def ask_ai(prompt: str, model: str = None) -> str:

    if PROVIDER == "ollama":
        return ask_ollama(prompt)
    if PROVIDER == "openai":
        return ask_openai(prompt, model)

    raise ValueError(f"Unknown AI provider: {PROVIDER}")

def ensure_model():
    models = ollama.list()
    names = [m.model for m in models.models]
    if MODEL not in names:
        for progress in ollama.pull(MODEL, stream=True):
            status = progress.get("status", "")
            total  = progress.get("total", 0)
            completed = progress.get("completed", 0)
            if total and completed is not None:
                percent = int(completed / total * 100)
                print(f"\r\033[KDev • {status} {percent}%", end="", flush=True)
        print()

ensure_model()

if __name__ == "__main__":
    while True:
        prompt = input("YOU > ").strip()

        if prompt.lower() in ("exit", "quit"):
            break

        print("\nDEV >")
        print(ask_ai(prompt))
        print()
