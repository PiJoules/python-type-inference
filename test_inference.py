import unittest

from inference import ModuleEnv
from pytype import *


def first(x):
    return next(iter(x))


class TestInference(unittest.TestCase):
    def test_assign(self):
        """
        Test variable assignment
        """
        code = """
x = 2
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

    def test_free_function_call(self):
        """
        Test calls to free functions.
        """
        code = """
def func(a):
    return a + 2
x = func(5)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

        # Function
        func = first(env.lookup("func"))
        self.assertSetEqual(
            func.returns(),
            {IntType()}
        )

        # Function env
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {IntType()}
        )

    def test_function_recursion(self):
        """
        Test correct types in recursive functions.
        """
        code = """
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)
x = fib(5)
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored var
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

        # Function env
        func = first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            func.env().exclusive_lookup("n"),
            {IntType()}
        )

        # Function return type
        self.assertSetEqual(
            func.returns(),
            {IntType()}
        )

        # fib() not in func env
        self.assertRaises(KeyError, func.env().exclusive_lookup, "fib")

        # fib() in module env
        self.assertSetEqual(
            func.env().lookup("fib"),
            env.exclusive_lookup("fib")
        )


if __name__ == "__main__":
    unittest.main()
