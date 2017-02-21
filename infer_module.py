import inference


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument("filename", help="Module to infer types from")

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    with open(args.filename, "r") as f:
        env = inference.ModuleEnv()
        env.parse_code(f.read())

    return 0


if __name__ == "__main__":
    main()
