#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *

import jedi


def main():
    sample = """
import keyword

class C:
    pass

class D:
    pass

x = D()
    """

    script = jedi.Script(sample)
    defs = script.goto_definitions()
    #defs = sorted(defs, key=lambda d: d.line)
    print(defs)

    return 0


if __name__ == "__main__":
    main()

