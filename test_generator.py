import unittest

from inference import ModuleEnv
from generator_type import GENERATOR_CLASS
from builtin_types import INT_TYPE
from builtin_types import NONE_TYPE


class TestGeneratorType(unittest.TestCase):
    def first(self, container):
        self.assertEqual(len(container), 1)
        return next(iter(container))

    def test_generator_from_function(self):
        """Test I can return a generator from a function."""
        code = """
def func():
    yield 1
    yield
x = func()
        """
        env = ModuleEnv()
        env.parse_code(code)

        expected = {GENERATOR_CLASS.instance(
            yields={INT_TYPE, NONE_TYPE}
        )}

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            expected
        )

    def test_generator_iteration(self):
        """Test that I can use the generator in a for loop."""
        code = """
def func():
    yield 1
    yield
for x in func():
    pass
        """
        env = ModuleEnv()
        env.parse_code(code)


if __name__ == "__main__":
    unittest.main()
