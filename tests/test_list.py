import unittest

from environment import ModuleEnv


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
            {LIST_CLASS.instance()}
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
            {LIST_CLASS.from_list([
                {STR_TYPE},
                {FLOAT_TYPE},
                {INT_TYPE},
            ])}
        )

    def test_list_equality(self):
        """Test various lists are equal."""
        # Multiple types of each contents
        self.assertSetEqual(
            {LIST_CLASS.from_list([
                {STR_TYPE},
            ])},
            {LIST_CLASS.from_list([
                {STR_TYPE},
                {STR_TYPE},
            ])}
        )

        # Order shouldn't matter
        self.assertSetEqual(
            {LIST_CLASS.from_list([
                {STR_TYPE},
                {INT_TYPE},
            ])},
            {LIST_CLASS.from_list([
                {INT_TYPE},
                {STR_TYPE},
            ])}
        )

        # Elements could be a combination of different types
        self.assertSetEqual(
            {LIST_CLASS.from_list([
                {INT_TYPE},
                {STR_TYPE},
            ])},
            {LIST_CLASS.from_list([
                {INT_TYPE, STR_TYPE}
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
            {INT_TYPE, FLOAT_TYPE}
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
            {LIST_CLASS.from_list([
                {INT_TYPE},
                {FLOAT_TYPE}
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
            {LIST_CLASS.from_list([
                {INT_TYPE, FLOAT_TYPE}
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
            {LIST_CLASS.from_list([
                {INT_TYPE}
            ])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {NONE_TYPE}
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
            {NONE_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.from_list([{INT_TYPE}])}
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
            {NONE_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.from_list([{
                FLOAT_TYPE, STR_TYPE,
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
            {NONE_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.from_list([{
                FLOAT_TYPE
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
            {FLOAT_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {FLOAT_TYPE}
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
            {LIST_CLASS.from_list([{FLOAT_TYPE}])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {NONE_TYPE}
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
            {FLOAT_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {FLOAT_TYPE}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z2"),
            {FLOAT_TYPE}
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
            {LIST_CLASS.from_list([{FLOAT_TYPE}])}
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
            {LIST_CLASS.from_list([{FLOAT_TYPE}])}
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
            {LIST_CLASS.from_list([{FLOAT_TYPE}])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            env.exclusive_lookup("y"),
        )


if __name__ == "__main__":
    unittest.main()
