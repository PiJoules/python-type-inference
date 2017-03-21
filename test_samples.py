import unittest

from inference import ModuleEnv
from tuple_type import TupleType
from module_type import *
from pytype import *
from float_type import FLOAT_CLASS
from int_type import INT_CLASS


class TestSamples(unittest.TestCase):
    def get_module_env(self, filepath):
        with open(filepath, "r") as f:
            env = ModuleEnv(module_location=filepath)
            env.parse_code(f.read())
            return env

    def first(self, container):
        self.assertEqual(len(container), 1)
        return next(iter(container))

    def test_fib(self):
        """Testing fib.py"""
        env = self.get_module_env("samples/fib.py")

        # main()
        main = self.first(env.exclusive_lookup("main"))
        self.assertSetEqual(
            main.returns(),
            {INT_CLASS.instance()}
        )

        # fib()
        fib = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            fib.env().exclusive_lookup("n"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            fib.returns(),
            {INT_CLASS.instance()}
        )

    def test_degrees(self):
        """Testing degrees.py"""
        env = self.get_module_env("samples/degrees.py")

        # math module
        self.assertSetEqual(
            env.exclusive_lookup("math"),
            {MathModuleType()}
        )

        # Conversion functions
        d2r_env = self.first(env.exclusive_lookup("degrees_to_radians")).env()
        self.assertSetEqual(
            d2r_env.exclusive_lookup("degrees"),
            {FLOAT_CLASS.instance()}
        )
        r2d_env = self.first(env.exclusive_lookup("radians_to_degrees")).env()
        self.assertSetEqual(
            r2d_env.exclusive_lookup("radians"),
            {FLOAT_CLASS.instance()}
        )
        f2c_env = self.first(env.exclusive_lookup("fahrenheit_to_celsius")).env()
        self.assertSetEqual(
            f2c_env.exclusive_lookup("f"),
            {FLOAT_CLASS.instance()}
        )
        c2f_env = self.first(env.exclusive_lookup("celsius_to_fahrenheit")).env()
        self.assertSetEqual(
            c2f_env.exclusive_lookup("c"),
            {FLOAT_CLASS.instance()}
        )
        c2k_env = self.first(env.exclusive_lookup("celsius_to_kelvin")).env()
        self.assertSetEqual(
            c2k_env.exclusive_lookup("c"),
            {FLOAT_CLASS.instance()}
        )
        k2c_env = self.first(env.exclusive_lookup("kelvin_to_celsius")).env()
        self.assertSetEqual(
            k2c_env.exclusive_lookup("k"),
            {FLOAT_CLASS.instance()}
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
            {FLOAT_CLASS.instance()}
        )
        self.assertSetEqual(
            pil_env.exclusive_lookup("units"),
            {STR_TYPE}
        )

        # convert()
        convert_env = self.first(env.exclusive_lookup("convert")).env()
        self.assertSetEqual(
            convert_env.exclusive_lookup("value"),
            {FLOAT_CLASS.instance()}
        )
        self.assertSetEqual(
            convert_env.exclusive_lookup("units"),
            {STR_TYPE}
        )

        # process_line()
        pl_env = self.first(env.exclusive_lookup("process_line")).env()
        self.assertSetEqual(
            pl_env.exclusive_lookup("value"),
            {FLOAT_CLASS.instance()}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("units"),
            {STR_TYPE}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result"),
            {FLOAT_CLASS.instance()}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result_units"),
            {STR_TYPE}
        )

        # Variables under the if __name__ == "__main__"
        tup = TupleType(init_contents=tuple([{STR_TYPE}, {STR_TYPE}]))
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


if __name__ == "__main__":
    unittest.main()
