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
            env.lookup("x"),
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
            env.lookup("x"),
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
            func.env().lookup("a"),
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



if __name__ == "__main__":
    unittest.main()
