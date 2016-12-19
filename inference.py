#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *

import ast


def ast_from_code(code):
    return ast.parse(code)


"""
Literals
"""

def num_type(num):
    return "int"


def str_type(s):
    return "str"


def bytes_type(b):
    return "bytes"




def literal_type(node):
    """Wrapper for other literal functions."""
    if isinstance(node, ast.Num):
        return num_type(node)
    elif isinstance(node, ast.Str):
        return str_type(node)



def types_from_module(node):
    """Generate tree containing types of all variables in it."""
    pass


def main():
    sample = """
x = 2
y = 3
    """

    prettyparseprint(sample)

    return 0


if __name__ == "__main__":
    main()

