import unittest

from environment import ModuleEnv
from builtins_manager import BuiltinsManager


class TestListType(unittest.TestCase):
    def test_empty_list_creation(self):
        """Test that I can make an emptylist."""
        code = """
x = []
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().instance()}
        )

    def test_list_initial_contents(self):
        """Test list creation with the elements in it."""
        code = """
x = [1, 3.0, "a"]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([
                {env.builtins().str()},
                {env.builtins().float()},
                {env.builtins().int()},
            ])}
        )

    def test_list_equality(self):
        """Test various lists are equal."""
        # Multiple types of each contents
        builtins = BuiltinsManager()

        self.assertSetEqual(
            {builtins.list_cls().from_list([
                {builtins.str()},
            ])},
            {builtins.list_cls().from_list([
                {builtins.str()},
                {builtins.str()},
            ])}
        )

        # Order shouldn't matter
        self.assertSetEqual(
            {builtins.list_cls().from_list([
                {builtins.str()},
                {builtins.int()},
            ])},
            {builtins.list_cls().from_list([
                {builtins.int()},
                {builtins.str()},
            ])}
        )

        # Elements could be a combination of different types
        self.assertSetEqual(
            {builtins.list_cls().from_list([
                {builtins.int()},
                {builtins.str()},
            ])},
            {builtins.list_cls().from_list([
                {builtins.int(), builtins.str()}
            ])}
        )

    def test_list_indexing(self):
        """Test indexing a list."""
        code = """
x = [1, 3.0]
y = x[0]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().int(), env.builtins().float()}
        )

    def test_list_slicing(self):
        """Test slicing a list returns a copy of the list."""
        code = """
x = [1, 3.0]
y = x[0:1]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().list_cls().from_list([
                {env.builtins().int()},
                {env.builtins().float()}
            ])}
        )

    def test_list_concatenation(self):
        """Test addition of 2 lists."""
        code = """
x = [1] + [3.0]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([
                {env.builtins().int(), env.builtins().float()}
            ])}
        )

    def test_list_appending(self):
        """Test appending to a list."""
        code = """
y = [3]
x = []
z = x.append(2)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            env.exclusive_lookup("y")
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([
                {env.builtins().int()}
            ])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {env.builtins().none()}
        )

    def test_list_extend(self):
        """Test extending a list with an iterable."""
        code = """
x = []
y = x.extend([1])
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().none()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{env.builtins().int()}])}
        )

    def test_list_insert(self):
        """Test insertion into a list."""
        code = """
x = [2.0]
y = x.insert(1, "a")
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().none()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{
                env.builtins().float(), env.builtins().str(),
            }])}
        )

    def test_list_remove(self):
        """Test removing an item from a list."""
        code = """
x = [2.0]
y = x.remove(2.0)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().none()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{
                env.builtins().float()
            }])}
        )

    def test_list_pop(self):
        """Test popping from a list."""
        code = """
x = [2.0, 4.0]
y = x.pop()
z = x.pop(1)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().float()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {env.builtins().float()}
        )

    def test_list_clear(self):
        """Test clearing a list."""
        code = """
x = [2.0]
y = x.clear()
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{env.builtins().float()}])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().none()}
        )

    def test_list_clear(self):
        """Test clearing a list."""
        code = """
x = [2.0]
y = x.index(0)
z = x.index(0, 1)
z2 = x.index(0, 1, 3)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().float()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {env.builtins().float()}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z2"),
            {env.builtins().float()}
        )

    def test_list_sort(self):
        """Test sorting a list."""
        code = """
x = [2.0]
x.sort()
x.sort(key=2)
x.sort(reverse=False)
x.sort(key=2, reverse=True)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{env.builtins().float()}])}
        )

    def test_list_reverse(self):
        """Test reversing a list."""
        code = """
x = [2.0]
x.reverse()
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{env.builtins().float()}])}
        )

    def test_list_copy(self):
        """Test copying a list."""
        code = """
x = [2.0]
y = x.copy()
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().list_cls().from_list([{env.builtins().float()}])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            env.exclusive_lookup("y"),
        )


if __name__ == "__main__":
    unittest.main()
