import unittest

from inference import ModuleEnv
from pytype import *


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



if __name__ == "__main__":
    unittest.main()
