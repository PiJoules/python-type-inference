from instance_type import InstanceType
from class_type import DynamicClassType
from pytype import PyType
from arguments import Arguments
from magic_methods import *
from function_type import FunctionType


class IntegerInterpetationError(TypeError):
    def __init__(self, t):
        super().__init__("'{}' object cannot be interpretted as an integer".format(t))


LIST_NAME = "list"


class ListType(InstanceType):
    def __init__(self, builtins, init_contents=None, **kwargs):
        """
        Args:
            init_contents (Optional[set[PyType]])
        """
        super().__init__(LIST_NAME, builtins, **kwargs)
        self.__contents = init_contents or set()
        assert isinstance(self.__contents, set)
        assert all(isinstance(x, PyType) for x in self.__contents)

    def append(self, item):
        assert isinstance(item, PyType)
        self.__contents.add(item)

    def extend(self, iterable_t):
        for iter_t in iterable_t.call_iter(Arguments.empty(self.builtins())):
            self.__contents |= iter_t.call_next(Arguments.empty(self.builtins()))

    def contents(self):
        """
        Returns:
            set[pytype.PyType]: Set of all types in the contents
        """
        return self.__contents

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        if not isinstance(other, ListType):
            return False

        return self.contents() == other.contents()

    def __bool__(self):
        return bool(self.contents())

    def __str__(self):
        str_contents = list(map(str, self.contents()))
        return "{}{}".format(self.name(), str_contents)


class ListGetItemMethod(GetItemMethod):
    def returns(self):
        self_types = self.env().lookup("self")
        key_types = self.env().lookup("key")
        results = set()
        for self_t in self_types:
            for key_t in key_types:
                if key_t.is_type(self.builtins().int()):
                    # Accessing 1 item in the tuple
                    results |= self_t.contents()
                elif key_t.is_type(self.builtins().slice()):
                    results.add(self_t)
                else:
                    raise RuntimeError("Unable to index {} with key {}".format(self_t, key_t))

        return results


class ListAddMethod(AddMethod):
    def returns(self):
        results = set()
        self_types = self.env().lookup("self")
        other_types = self.env().lookup("other")

        for self_t in self_types:
            for other_t in other_types:
                if other_t.is_type(self.builtins().list()):
                    results.add(self.builtins().list_cls().merge_lists(self_t, other_t))
                else:
                    raise RuntimeError("Unable to concatenate list with {}".format(other_t))

        return results

class ListAppendMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "append", builtins,
            pos_args=["self", "x"],
        )

    def returns(self):
        self_types = self.env().lookup("self")
        val_types = self.env().lookup("x")

        for self_t in self_types:
            for val_t in val_types:
                self_t.append(val_t)

        return {self.builtins().none()}

class ListExtendMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "extend", builtins,
            pos_args=["self", "iterable"]
        )

    def returns(self):
        self_types = self.env().lookup("self")
        iterable_types = self.env().lookup("iterable")

        for self_t in self_types:
            for iterable_t in iterable_types:
                self_t.extend(iterable_t)

        return {self.builtins().none()}

class ListIterMethod(IterMethod):
    def returns(self):
        results = set()
        self_types = self.env().lookup("self")

        for self_t in self_types:
            results |= self_t.contents()

        return {self.builtins().generator_cls().instance(yields=results)}


class ListInsertMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "insert", builtins,
            pos_args=["self", "i", "x"]
        )

    def returns(self):
        self_types = self.env().lookup("self")
        i_types = self.env().lookup("i")
        x_types = self.env().lookup("x")

        for self_t in self_types:
            for i_t in i_types:
                if not i_t.is_type(self.builtins().int()):
                    raise IntegerInterpetationError(i_t)
                for x_t in x_types:
                    self_t.append(x_t)

        return {self.builtins().none()}


class ListRemoveMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "remove", builtins,
            pos_args=["self", "x"]
        )

    def returns(self):
        return {self.builtins().none()}


class ListPopMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "pop", builtins,
            pos_args=["self"],
            keywords=["i"],
            keyword_defaults=[{builtins.int()}],
        )

    def returns(self):
        env = self.env()
        self_types = env.lookup("self")
        i_types = env.lookup("i")

        results = set()

        for self_t in self_types:
            for i_t in i_types:
                if not i_t.is_type(self.builtins().int()):
                    raise IntegerInterpetationError(i_t)
                else:
                    results |= self_t.contents()

        return results

class ListClearMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "clear", builtins,
            pos_args=["self"]
        )

    def returns(self):
        return {self.builtins().none()}


class ListIndexMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "index", builtins,
            pos_args=["self", "x"],
            keywords=["start", "end"],
            keyword_defaults=[{builtins.int()}, {builtins.int()}]
        )

    def returns(self):
        self_types = self.env().lookup("self")
        results = set()
        for self_t in self_types:
            results |= self_t.contents()
        return results


class ListSortMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "sort", builtins,
            pos_args=["self"],
            keywords=["key", "reverse"],
            keyword_defaults=[{builtins.none()}, {builtins.bool()}]
        )

    def returns(self):
        return {self.builtins().none()}


class ListReverseMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "reverse", builtins,
            pos_args=["self"]
        )

    def returns(self):
        return {self.builtins().none()}


class ListCopyMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "copy", builtins,
            pos_args=["self"]
        )

    def returns(self):
        return self.env().lookup("self")


class ListClass(DynamicClassType):
    def __init__(self, builtins, **kwargs):
        super().__init__(
            builtins, ListType,
            init_methods=(
                ListGetItemMethod(builtins),
                ListAddMethod(builtins),
                ListIterMethod(builtins),
                ListAppendMethod(builtins),
                ListExtendMethod(builtins),
                ListInsertMethod(builtins),
                ListRemoveMethod(builtins),
                ListPopMethod(builtins),
                ListClearMethod(builtins),
                ListIndexMethod(builtins),
                ListSortMethod(builtins),
                ListReverseMethod(builtins),
                ListCopyMethod(builtins),
            ),
            **kwargs
        )

    def from_list(self, lst):
        contents = set()
        for types in lst:
            contents |= types
        return self.instance(init_contents=contents)

    def merge_lists(self, *lsts):
        contents = set()
        for lst in lsts:
            contents |= lst.contents()
        return self.from_list([contents])
