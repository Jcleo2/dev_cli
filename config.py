import os
import getpass
import keyring

CONFIG_DIR = os.path.expanduser("~/.dev")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")


def load_speed():
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if line.startswith("speed="):
                return line.strip().split("=", 1)[1]

    return None


def save_speed(speed):
    os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        f.write(f"speed={speed}\n")


def setup_openai_key():
    print()
    print("OpenAI API Key")
    print("--------------")

    key = getpass.getpass("Enter API key:  ").strip()

    if not key:
        print("\nNo API key entered.")
        return

    keyring.set_password("DEV", "openai_api_key", key)

    print("\nOpenAI API key saved securely")

def choose_selection():
    current = load_speed()

    print()
    print("DEV Preferences")
    print("----------------")
    print(f"Current AI profile: {current or 'Not set'}")
    print()
    print("1. BLAZING")
    print("2. FASTER")
    print("3. MOST POWERFUL")
    print()
    print()
    print()
    print("4. OpenAI API key")
    print("5. Exit")

    choice = input("\nChoose: ")

    if choice == "1":
        save_speed("blazing")
        print("\nAI profile set to BLAZING.")

    elif choice == "2":
        save_speed("faster")
        print("\nAI profile set to FASTER.")

    elif choice == "3":
        save_speed("powerful")
        print("\nAI profile set to MOST POWERFUL.")

    elif choice == "4":
        setup_openai_key()

    elif choice == "5":
        return

    else:
        print("\nInvalid choice.")


if __name__ == "__main__":
    choose_selection()
