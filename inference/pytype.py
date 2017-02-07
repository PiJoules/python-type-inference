# -*- coding: utf-8 -*-

import inference.pyinstance


class PyType:
    """
    Object meant to hold the attributes of an instance.

    This is nonexistant to the module environment at runtime.
    """

    def __init__(self):
        self.__attrs = {}  # dict[str, set[Instance]]

    def get_attr(self, attr):
        """
        Returns:
            set[Instance]

        Raises:
            RuntimeError
        """
        if attr not in self.__attrs:
            raise RuntimeError("Attr '{}' was not previously added to type '{}'".format(attr, self.name()))
        return self.__attrs[attr]

    def set_attr(self, attr, val):
        """
        Args:
            attr (str)
            val (set[Instance])
        """
        assert isinstance(val, set)
        assert all(isinstance(x, inference.pyinstance) for x in val)
        self.__attrs[attr] = val
