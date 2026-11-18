import base64 as py_base64 


def run(args):
    if len(args) < 2:
        print("Usage: dev base64 <encode|decode> <text>")
        return


    mode = args[0]
    text = " ".join(args[1:])

    if mode == "encode":
        encoded = py_base64.b64encode(text.encode()).decode()
        print(encoded)


    elif mode == "decode":
        try:
            decoded = py_base64.b64decode(text).decode()
            print(decoded)

        except Exception:
            print("Invalid Base64.")


    else:
        print("Usage: dev base64 <encode|decode> <text>")


if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
