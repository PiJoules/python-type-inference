# -*- coding: utf-8 -*-


class Type(object):
    def evaluate(self):
        """
        Return some delayed evaluation of what this type represents.

        The result must be hashable.
        """
        raise NotImplementedError

    def __str__(self):
        return str(self.evaluate())

    def __eq__(self, other):
        return self.evaluate() == other.evaluate()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.evaluate())

    def clone(self):
        raise NotImplementedError


class BaseType(Type):
    def __init__(self, base_type: str) -> None:
        self.__base_type = base_type

    def evaluate(self):
        """
        Returns:
            str
        """
        return self.__base_type

    def clone(self):
        return BaseType(self.__base_type)


class AnyType(BaseType):
    def __init__(self):
        super().__init__("Any")


class BoolType(BaseType):
    def __init__(self):
        super().__init__("bool")


class IntType(BaseType):
    def __init__(self):
        super().__init__("int")


class FloatType(BaseType):
    def __init__(self):
        super().__init__("float")


class ComplexType(BaseType):
    def __init__(self):
        super().__init__("complex")


class StrType(BaseType):
    def __init__(self):
        super().__init__("str")


class BytesType(BaseType):
    def __init__(self):
        super().__init__("bytes")


class NoneType(BaseType):
    def __init__(self):
        super().__init__("None")


class MultiType(Type):
    """
    Class for performing delayed evaluation of types.
    This is a container of strings that is lazily evaluated.
    """
    def __init__(self, base_type=None):
        """
        Args:
            base_type (Type): Another type that this type is equivalent to.
        """
        if base_type is None:
            self.__types = []  # type: list[Type]
        elif isinstance(base_type, list):
            self.__types = base_type
        else:
            self.__types = [base_type]

    def evaluate(self):
        """
        Returns:
            frozenset[(str, Container, Mapping)]: Types of variables
        """
        if not self.__types:
            return "Any"
        elif len(self.__types) == 1:
            return self.__types[0].evaluate()

        types = set()
        for t in self.__types:
            if isinstance(t, MultiType):
                evaluated_t = t.evaluate()
                if isinstance(evaluated_t, frozenset):
                    # Merge any multitypes
                    types |= evaluated_t
                else:
                    types.add(evaluated_t)
            elif isinstance(t, (BaseType, Container, Mapping)):
                types.add(t.evaluate())
            else:
                raise RuntimeError("Unexpected type '{}'".format(type(t)))

        if "Any" in types:
            # Any type dominates the rest
            return "Any"

        return frozenset(types)

    def update(self, other: Type):
        """Update the types in this container."""
        self.__types.append(other)

    def replace(self, other):
        """Replace all types in this container with another list of types."""
        self.__types = other

    def clone(self):
        return MultiType([x for x in self.__types])


class Container(Type):
    def __init__(self, init_type:MultiType=None) -> None:
        self.__content = init_type or MultiType()

    def evaluate(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 1 with the only element
                representing the types of the contents.
        """
        return (self.__content.evaluate(), )

    def add(self, t):
        """Add a new type into the container."""
        self.__content.update(t)

    def clone(self):
        return Container(self.__content)


class Mapping(Type):
    def __init__(self, init_key_type:MultiType=None, init_val_type:MultiType=None):
        self.__key = init_key_type or MultiType()
        self.__val = init_val_type or MultiType()

    def evaluate(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 2 with the first element
                representing the key types and the second representing the
                value types.
        """
        return (self.__key.evaluate(), self.__val.evaluate())

    def add_key(self, key_type):
        self.__key.update(key_type)

    def add_val(self, val_type):
        self.__val.update(val_type)

    def clone(self):
        return Mapping(self.__key, self.__val)


