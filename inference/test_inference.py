#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import inference


class TestTypeInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int"})

    def test_multiple_assignment(self):
        """Test assignment of multiple types to the same variable."""
        code = """
x = 2
x = "string"
x = 3
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int", "str"})

    def test_function_definition(self):
        """Test function definitions."""
        code = """
def func():
    return 2
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.simple_lookup("func").return_type(), {"int"})

    def test_func_def_default_args(self):
        """Test function definition with an argument and the function is not called."""
        code = """
def func(arg):
    return arg
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.simple_lookup("func").return_type(), {"Any"})

    def test_func_def_keyword_args(self):
        """Test function definition with default keyword arguments."""
        code = """
def func(arg=2):
    return arg
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.simple_lookup("func").return_type(), {"int"})

    def test_func_def_varargs(self):
        """Test function definition with variable arguments (*args)."""
        code = """
def func(*args):
    return args
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.simple_lookup("func").return_type(), {"tuple"})
        self.assertSetEqual(
            env.simple_lookup("func").environment().simple_lookup("args")
            .contents(),
            {"Any"}
        )

    def test_func_def_varargs(self):
        """Test function definition with **kwargs."""
        code = """
def func(**kwargs):
    return kwargs
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.simple_lookup("func").return_type(), {"dict"})
        self.assertSetEqual(
            env.simple_lookup("func").environment().simple_lookup("kwargs")
            .value_contents(),
            {"Any"}
        )
        self.assertSetEqual(
            env.simple_lookup("func").environment().simple_lookup("kwargs")
            .key_contents(),
            {"Any"}
        )




if __name__ == "__main__":
    unittest.main()


