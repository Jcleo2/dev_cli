import json 
import sys 


def run(arg):
    if not arg:
        print("Usage: dev json <file>")
        return


    filename = arg[0]

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        print(json.dumps(data, indent=2))

    except FileNotFoundError:
        print(f"File not found: {filename}")

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")



if __name__ == "__main__":
    run(sys.argv[1:])
