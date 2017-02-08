# -*- coding: utf-8 -*-


class Instance:
    """
    Instance available at runtime.
    """

    def __init__(self, type_name, init_attrs=None):
        self.__type_name = type_name
        self.__attrs = init_attrs or {}  # dict[str, set[Instance]]

    def type_name(self):
        """
        Returns:
            str
        """
        return self.__type_name

    def __hash__(self):
        return hash(self.type_name())

    def __eq__(self, other):
        """
        All instances created at runtime are unique and are always different,
        so this will be determined by the id.
        """
        return id(self) == id(other)

    def __ne__(self, other):
        return not (self == other)

    def call(self, args=None):
        """
        Call this instance with arguments.

        Args:
            args (Optional[PyArguments])

        Returns:
            set[Instance]
        """
        raise NotImplementedError("Instance of type '{}' is not callable".format(self.type_name()))

    def get_attr(self, attr):
        """
        Returns:
            set[Instance]
        """
        if attr not in self.__attrs:
            raise RuntimeError("No attr '{}' found in instance of '{}'".format(attr, self.type_name()))
        return self.__attrs[attr]

    def set_attr(self, attr, vals):
        """
        Args:
            attr (self)
            vals (set[Instance])
        """
        assert isinstance(vals, set)
        assert all(isinstance(x, Instance) for x in vals)

        if attr not in self.__attrs:
            self.__attrs[attr] = set(vals)
        else:
            self.__attrs[attr] |= vals


class ClassInstance(Instance):
    """
    Just like a regular instance, this is an instance for creating other instances.

    This is the base one which represents the type 'type'.
    """

    def __init__(self):
        super().__init__("type")


"""
Builtin types
"""


def load_builtin_variables():
    """
    Load all instances available at runtime.

    Returns:
        dict[str, set[Instance]]
    """
    from .builtin_insts import INT_CLASS

    return {
        "int": {INT_CLASS},
    }

