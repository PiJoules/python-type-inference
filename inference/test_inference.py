#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from inference import Environment, simple


class TestTypeInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int"})

    def test_multiple_assignment(self):
        """Test assignment of multiple types to the same variable."""
        code = """
x = 2
x = "string"
x = 3
        """
        env = Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int", "str"})

    def test_function_definition(self):
        """Test function definitions."""
        code = """
def func():
    return 2
        """
        env = Environment.from_code(code)

        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_def_default_args(self):
        """Test function definition with an argument and the function is not called."""
        code = """
def func(arg):
    return arg
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("arg")).value(),
            "Any"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "Any"
        )

    def test_func_def_keyword_args(self):
        """Test function definition with default keyword arguments."""
        code = """
def func(arg=2):
    return arg
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("arg")).value(),
            "int"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_def_varargs(self):
        """Test function definition with variable arguments (*args)."""
        code = """
def func(*args):
    return args
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("args")).value(),
            "tuple"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "tuple"
        )
        # Tuple contents
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("args"))
            .contents()).value(),
            "Any"
        )

    def test_func_def_kwargs(self):
        """Test function definition with **kwargs."""
        code = """
def func(**kwargs):
    return kwargs
        """
        env = Environment.from_code(code)

        # Arguments
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("kwargs")).value(),
            "dict"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "dict"
        )
        # Dict contents
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .value_contents()).value(),
            "Any"
        )
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .key_contents()).value(),
            "Any"
        )

    def test_func_call_positional(self):
        """Test new argument types by function call arguments."""
        code = """
def func(arg):
    return arg

x = func(2)
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "int"
        )
        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("arg")).value(),
            "int"
        )
        # Return value
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_call_keyword(self):
        """Test new argument types by function call arguments with keyword arguments."""
        code = """
def func(arg=1.0):
    return arg

x = func(arg=2)
        """
        env = Environment.from_code(code)



if __name__ == "__main__":
    unittest.main()


