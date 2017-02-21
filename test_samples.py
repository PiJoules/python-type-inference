import unittest

from inference import ModuleEnv


class TestSamples(unittest.TestCase):
    def __get_module_env(self, filepath):
        with open(filepath, "r") as f:
            env = ModuleEnv()
            env.parse_code(f.read())
            return env

    def test_fib(self):
        """Testing fib.py"""
        env = self.__get_module_env("samples/fib.py")

