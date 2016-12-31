# -*- coding: utf-8 -*-

import objects


class Type(object):
    """
    Types declared in an environment.

    A Type respresents a type that a variable can be and any attributes
    it can hold (equivalent to a C struct).

    A Type is not accessible in the env at runtime and acts only as meta data
    used by someone analyzing the program.

    Every time an attribute of this type is set, it is added to this Type.

    For each type, there must be a corresponding object.
    """
    def __init__(self, name, obj_cls, init_attrs=None):
        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[Object]]
        self.__obj_cls = obj_cls

        # Type checks
        assert isinstance(self.__attrs, dict)
        assert all(isinstance(x, set) for x in self.__attrs.values())
        for s in self.__attrs:
            assert all(isinstance(x, objects.Object) for x in s)

    def name(self):
        """String representing the name of the type."""
        return self.__name

    def attrs(self):
        """
        Returns:
            dict[str, set[Object]]
        """
        return self.__attrs

    def get_attr(self, attr):
        """
        Returns:
            set[Object]

        Raises:
            RuntimeError
        """
        val = self.__attrs.get(attr, None)
        if val is None:
            raise RuntimeError("Attribute '{}' does not exist in type '{}'".format(attr, self.name()))
        return val

    def set_attr(self, attr, val):
        """
        Args:
            attr (str)
            val (set[Object])
        """

        # Type checks
        assert isinstance(val, set)
        assert all(isinstance(x, objects.Object) for x in val)

        # Add the type
        if attr in self.__attrs:
            self.__attrs[attr] |= val
        else:
            self.__attrs[attr] = val

    def new_obj(self, *args, **kwargs):
        """Returns a new instance of some object."""
        return self.__obj_cls(self, *args, **kwargs)


"""
Builtin Types
"""
class IntType(Type):
    def __init__(self):
        return super().__init__("int", objects.IntObject)

class FloatType(Type):
    def __init__(self):
        return super().__init__("float", objects.FloatObject)


class ListType(Type):
    """
    Since lists are builtin to the interpetter and not written in python
    source code, wrappers will need to be made to manually keep track of the
    content types.
    """
    def __init__(self):
        return super().__init__("list", objects.ListObject)


class FunctionType(Type):
    def __init__(self):
        return super().__init__("function", objects.FunctionObject)


