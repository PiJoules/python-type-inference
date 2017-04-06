import unittest

from inference import ModuleEnv
from tuple_type import TUPLE_CLASS
from module_type import *
from pytype import *
from builtin_types import *
from function_type import FunctionType


class TestSamples(unittest.TestCase):
    def create_module_env(self, filepath):
        with open(filepath, "r") as f:
            env = ModuleEnv(module_location=filepath)
            env.parse_code(f.read())
            return env

    def first(self, container):
        self.assertEqual(len(container), 1)
        return next(iter(container))

    def test_fib(self):
        """Testing fib.py"""
        env = self.create_module_env("samples/fib.py")

        # main()
        main = self.first(env.exclusive_lookup("main"))
        self.assertSetEqual(
            main.returns(),
            {INT_TYPE}
        )

        # fib()
        fib = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            fib.env().exclusive_lookup("n"),
            {INT_TYPE}
        )
        self.assertSetEqual(
            fib.returns(),
            {INT_TYPE}
        )

    def test_degrees(self):
        """Testing degrees.py"""
        env = self.create_module_env("samples/degrees.py")

        # math module
        self.assertSetEqual(
            env.exclusive_lookup("math"),
            {MathModuleType()}
        )

        # Conversion functions
        d2r_env = self.first(env.exclusive_lookup("degrees_to_radians")).env()
        self.assertSetEqual(
            d2r_env.exclusive_lookup("degrees"),
            {FLOAT_TYPE}
        )
        r2d_env = self.first(env.exclusive_lookup("radians_to_degrees")).env()
        self.assertSetEqual(
            r2d_env.exclusive_lookup("radians"),
            {FLOAT_TYPE}
        )
        f2c_env = self.first(env.exclusive_lookup("fahrenheit_to_celsius")).env()
        self.assertSetEqual(
            f2c_env.exclusive_lookup("f"),
            {FLOAT_TYPE}
        )
        c2f_env = self.first(env.exclusive_lookup("celsius_to_fahrenheit")).env()
        self.assertSetEqual(
            c2f_env.exclusive_lookup("c"),
            {FLOAT_TYPE}
        )
        c2k_env = self.first(env.exclusive_lookup("celsius_to_kelvin")).env()
        self.assertSetEqual(
            c2k_env.exclusive_lookup("c"),
            {FLOAT_TYPE}
        )
        k2c_env = self.first(env.exclusive_lookup("kelvin_to_celsius")).env()
        self.assertSetEqual(
            k2c_env.exclusive_lookup("k"),
            {FLOAT_TYPE}
        )

        # read_input()
        read_input_env = self.first(env.exclusive_lookup("read_input")).env()
        self.assertSetEqual(
            read_input_env.exclusive_lookup("input_line"),
            {STR_TYPE}
        )
        self.assertSetEqual(
            read_input_env.exclusive_lookup("output_line"),
            {STR_TYPE}
        )

        # parse_input_line()
        pil_env = self.first(env.exclusive_lookup("parse_input_line")).env()
        self.assertSetEqual(
            pil_env.exclusive_lookup("value"),
            {FLOAT_TYPE}
        )
        self.assertSetEqual(
            pil_env.exclusive_lookup("units"),
            {STR_TYPE}
        )

        # convert()
        convert_env = self.first(env.exclusive_lookup("convert")).env()
        self.assertSetEqual(
            convert_env.exclusive_lookup("value"),
            {FLOAT_TYPE}
        )
        self.assertSetEqual(
            convert_env.exclusive_lookup("units"),
            {STR_TYPE}
        )

        # process_line()
        pl_env = self.first(env.exclusive_lookup("process_line")).env()
        self.assertSetEqual(
            pl_env.exclusive_lookup("value"),
            {FLOAT_TYPE}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("units"),
            {STR_TYPE}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result"),
            {FLOAT_TYPE}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result_units"),
            {STR_TYPE}
        )

        # Variables under the if __name__ == "__main__"
        tup = TUPLE_CLASS.create_tuple(init_contents=tuple([{STR_TYPE}, {STR_TYPE}]))
        self.assertSetEqual(
            env.exclusive_lookup("input_lines"),
            {tup}
        )
        self.assertSetEqual(
            env.exclusive_lookup("line"),
            {STR_TYPE}
        )
        self.assertSetEqual(
            env.exclusive_lookup("e"),
            env.lookup("ValueError")
        )

    def test_disemvowel(self):
        """Test disemvowel.py"""
        env = self.create_module_env("samples/disemvowel.py")

        self.assertSetEqual(
            env.exclusive_lookup("__name__"),
            {STR_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("words"),
            {STR_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("words"),
            {STR_TYPE}
        )

        disemv_func = self.first(env.exclusive_lookup("disemvowel"))
        func_env = disemv_func.env()
        self.assertSetEqual(
            disemv_func.returns(),
            {TUPLE_CLASS.instance(init_contents=(
                {STR_TYPE}, {STR_TYPE}
            ))}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("vowels"),
            {STR_TYPE}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("consonants"),
            {STR_TYPE}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("c"),
            {STR_TYPE}
        )


if __name__ == "__main__":
    unittest.main()
