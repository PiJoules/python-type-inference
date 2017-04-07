import unittest

from environment import ModuleEnv
from module_type import *


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
            {env.builtins().int()}
        )

        # fib()
        fib = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            fib.env().exclusive_lookup("n"),
            {env.builtins().int()}
        )
        self.assertSetEqual(
            fib.returns(),
            {env.builtins().int()}
        )

    def test_degrees(self):
        """Testing degrees.py"""
        env = self.create_module_env("samples/degrees.py")

        # math module
        self.assertSetEqual(
            env.exclusive_lookup("math"),
            {MathModuleType(env.builtins())}
        )

        # Conversion functions
        d2r_env = self.first(env.exclusive_lookup("degrees_to_radians")).env()
        self.assertSetEqual(
            d2r_env.exclusive_lookup("degrees"),
            {env.builtins().float()}
        )
        r2d_env = self.first(env.exclusive_lookup("radians_to_degrees")).env()
        self.assertSetEqual(
            r2d_env.exclusive_lookup("radians"),
            {env.builtins().float()}
        )
        f2c_env = self.first(env.exclusive_lookup("fahrenheit_to_celsius")).env()
        self.assertSetEqual(
            f2c_env.exclusive_lookup("f"),
            {env.builtins().float()}
        )
        c2f_env = self.first(env.exclusive_lookup("celsius_to_fahrenheit")).env()
        self.assertSetEqual(
            c2f_env.exclusive_lookup("c"),
            {env.builtins().float()}
        )
        c2k_env = self.first(env.exclusive_lookup("celsius_to_kelvin")).env()
        self.assertSetEqual(
            c2k_env.exclusive_lookup("c"),
            {env.builtins().float()}
        )
        k2c_env = self.first(env.exclusive_lookup("kelvin_to_celsius")).env()
        self.assertSetEqual(
            k2c_env.exclusive_lookup("k"),
            {env.builtins().float()}
        )

        # read_input()
        read_input_env = self.first(env.exclusive_lookup("read_input")).env()
        self.assertSetEqual(
            read_input_env.exclusive_lookup("input_line"),
            {env.builtins().str()}
        )
        self.assertSetEqual(
            read_input_env.exclusive_lookup("output_line"),
            {env.builtins().str()}
        )

        # parse_input_line()
        pil_env = self.first(env.exclusive_lookup("parse_input_line")).env()
        self.assertSetEqual(
            pil_env.exclusive_lookup("value"),
            {env.builtins().float()}
        )
        self.assertSetEqual(
            pil_env.exclusive_lookup("units"),
            {env.builtins().str()}
        )

        # convert()
        convert_env = self.first(env.exclusive_lookup("convert")).env()
        self.assertSetEqual(
            convert_env.exclusive_lookup("value"),
            {env.builtins().float()}
        )
        self.assertSetEqual(
            convert_env.exclusive_lookup("units"),
            {env.builtins().str()}
        )

        # process_line()
        pl_env = self.first(env.exclusive_lookup("process_line")).env()
        self.assertSetEqual(
            pl_env.exclusive_lookup("value"),
            {env.builtins().float()}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("units"),
            {env.builtins().str()}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result"),
            {env.builtins().float()}
        )
        self.assertSetEqual(
            pl_env.exclusive_lookup("result_units"),
            {env.builtins().str()}
        )

        # Variables under the if __name__ == "__main__"
        tup = env.builtins().tuple_cls().instance(init_contents=tuple([{env.builtins().str()}, {env.builtins().str()}]))
        self.assertSetEqual(
            env.exclusive_lookup("input_lines"),
            {tup}
        )
        self.assertSetEqual(
            env.exclusive_lookup("line"),
            {env.builtins().str()}
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
            {env.builtins().str()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("words"),
            {env.builtins().str()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("words"),
            {env.builtins().str()}
        )

        disemv_func = self.first(env.exclusive_lookup("disemvowel"))
        func_env = disemv_func.env()
        self.assertSetEqual(
            disemv_func.returns(),
            {env.builtins().tuple_cls().instance(init_contents=(
                {env.builtins().str()}, {env.builtins().str()}
            ))}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("vowels"),
            {env.builtins().str()}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("consonants"),
            {env.builtins().str()}
        )

        self.assertSetEqual(
            func_env.exclusive_lookup("c"),
            {env.builtins().str()}
        )


if __name__ == "__main__":
    unittest.main()
