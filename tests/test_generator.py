import unittest

from environment import ModuleEnv


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

        expected = {env.builtins().generator_cls().instance(
            yields={env.builtins().int(), env.builtins().none()}
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
