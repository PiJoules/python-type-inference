#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inference as inf
import json


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument("filename", help="Python file to dump.")

    return parser.parse_args()


def main():
    args = get_args()

    with open(args.filename, "r") as f:
        print(json.dumps(inf.Environment.from_code(f.read()).json(), indent=4))

    return 0


if __name__ == "__main__":
    main()

