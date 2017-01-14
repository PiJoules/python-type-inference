#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from inference import *


class TestInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

    def test_function_call(self):
        """Test function calls."""
        code = """
def func():
    return 2
x = func()
        """
        env = Environment()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("func")).returns(),
            {IntInst()}
        )

    def test_function_arg_call(self):
        """Test that the arguments influence the return type."""
        code = """
def func(a):
    return a
x = func(2)
        """
        env = Environment()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("func")).returns(),
            {IntInst()}
        )

        # Argument in function
        self.assertSetEqual(
            first(env.lookup("func")).env().lookup("a"),
            {IntInst()}
        )

    def test_function_recursion(self):
        """Assert correct types in recursive functions."""
        code = """
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)
x = fib(5)
        """
        env = Environment()
        env.parse_code(code)



if __name__ == "__main__":
    unittest.main()

