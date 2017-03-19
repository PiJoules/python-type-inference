import unittest

from inference import ModuleEnv
from tuple_type import TupleType
from test_inference import first
from pytype import *


class TestSamples(unittest.TestCase):
    def __get_module_env(self, filepath):
        with open(filepath, "r") as f:
            env = ModuleEnv(module_location=filepath)
            env.parse_code(f.read())
            return env

    def test_fib(self):
        """Testing fib.py"""
        env = self.__get_module_env("samples/fib.py")

        # main()
        main = first(env.exclusive_lookup("main"))
        self.assertSetEqual(
            main.returns(),
            {IntType()}
        )

        # fib()
        fib = first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            fib.env().exclusive_lookup("n"),
            {IntType()}
        )
        self.assertSetEqual(
            fib.returns(),
            {IntType()}
        )

    def test_degrees(self):
        """Testing degrees.py"""
        env = self.__get_module_env("samples/degrees.py")

        # Variables under the if __name__ == "__main__"
        tup = TupleType(init_contents=tuple([{STR_TYPE}, {STR_TYPE}]))
        self.assertSetEqual(
            env.exclusive_lookup("input_lines"),
            {tup}
        )

