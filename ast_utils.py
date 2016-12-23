# -*- coding: utf-8 -*-

"""
Utility functions.
"""

import ast


def prettyparsetext(code, spaces=4):
    """Nicer way of displaying the dump produced by ast.dump().
    Value is returned as string.

    Args:
        spaces (int): Number of spaces per indentation.
    """
    if isinstance(code, str):
        node = ast.parse(code)
    else:
        node = code
    text = ast.dump(node)
    indent_count = 0
    i = 0
    while i < len(text):
        c = text[i]

        if text[i:i+2] in ("()", "[]"):
            i += 1
        elif c in "([":
            indent_count += 1
            indentation = spaces*indent_count
            text = text[:i+1] + "\n" + " "*indentation + text[i+1:]
        elif c in ")]":
            indent_count -= 1
            indentation = spaces*indent_count
            text = text[:i] + "\n" + " "*indentation + text[i:]
            i += 1 + indentation

            if text[i:i+3] in ("), ", "], "):
                text = text[:i+2] + "\n" + " "*indentation + text[i+3:]
                i += indentation

        i += 1
    return text


def prettyparseprint(code, spaces=4):
    """Dump the results of prettyparsetext."""
    print(prettyparsetext(code, spaces=spaces))


def prettyparseprintfile(filename, spaces=4):
    """Dump the results of a file."""
    with open(filename, "r") as f:
        prettyparseprint(f.read(), spaces=spaces)


def generate_ast(code):
    """Generate a python ast from python code."""
    return ast.parse(code)


def ast_from_file(filename):
    """Generate a python ast from a python file."""
    with open(filename, "r") as f:
        return generate_ast(f.read())


