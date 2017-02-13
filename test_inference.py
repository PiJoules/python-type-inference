import unittest

from inference import ModuleEnv


class TestInference(unittest.TestCase):
    def test_assign(self):
        code = """
x = 2
"""
        env = ModuleEnv()
        env.parse_code(code)


if __name__ == "__main__":
    unittest.main()
