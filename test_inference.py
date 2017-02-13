import unittest

from inference import ModuleEnv
from pytype import *


class TestInference(unittest.TestCase):
    def test_assign(self):
        code = """
x = 2
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntType()}
        )


if __name__ == "__main__":
    unittest.main()
