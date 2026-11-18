import os
import getpass
import keyring

CONFIG_DIR = os.path.expanduser("~/.dev")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")


def load_config():
    settings = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    settings[key] = value
    return settings


def save_setting(key, value):
    settings = load_config()
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        for name, item in settings.items():
            f.write(f"{name}={item}\n")


def load_speed():
    return load_config().get("speed")


def save_speed(speed):
    save_setting("speed", speed)
    save_setting("ollama_model", None)


def setup_openai_key():
    print("\nOpenAI API Key")
    key = getpass.getpass("Enter API key: ").strip()
    if key:
        keyring.set_password("DEV", "openai_api_key", key)
        print("API key saved securely.")
    else:
        print("No API key entered.")


def choose_provider():
    print("\n1. Ollama")
    print("2. OpenAI")
    choice = input("Choose provider: ").strip()

    if choice == "1":
        save_setting("provider", "ollama")
    elif choice == "2":
        save_setting("provider", "openai")
    else:
        print("Invalid choice.")


def choose_model():
    settings = load_config()
    provider = settings.get("provider", "ollama")
    key = provider + "_model"
    default = "qwen3:8b" if provider == "ollama" else "gpt-4.1-mini"

    print(f"\nCurrent {provider} model: {settings.get(key, default)}")
    model = input("Model name: ").strip()

    if model:
        save_setting(key, model)
        print("Model saved.")


def choose_selection():
    while True:
        settings = load_config()
        provider = settings.get("provider", "ollama")
        default = "qwen3:8b" if provider == "ollama" else "gpt-4.1-mini"
        model = settings.get(provider + "_model", default)
        key = keyring.get_password("DEV", "openai_api_key")

        print("\nDEV Preferences")
        print("----------------")
        print(f"Provider: {provider}")
        print(f"Model: {model}")
        print(f"Ollama profile: {settings.get('speed', 'Not set')}")
        print(f"OpenAI API key: {'Configured' if key else 'Not configured'}")
        print("\n1. Change provider")
        print("2. Change model")
        print("3. Change Ollama speed")
        print("4. Set OpenAI API key")
        print("5. Exit")

        choice = input("\nChoose: ").strip()

        if choice == "1":
            choose_provider()
        elif choice == "2":
            choose_model()
        elif choice == "3":
            print("\n1. BLAZING\n2. FASTER\n3. MOST POWERFUL")
            speed = {"1": "blazing", "2": "faster", "3": "powerful"}
            selected = input("Choose: ").strip()
            if selected in speed:
                save_speed(speed[selected])
        elif choice == "4":
            setup_openai_key()
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    choose_selection()
