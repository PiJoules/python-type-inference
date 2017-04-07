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
                if other_t.is_type(cls.instance()):
                    results.add(cls.merge_lists(self_t, other_t))
                else:
                    raise RuntimeError("Unable to concatenate list with {}".format(other_t))

        return results

class ListAppendMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="append",
            pos_args=["self", "x"],
        )

    def adjusted_call(self, args):
        self.check_pos_args(args)

        self_types, val_types = args.pos_args()

        for self_t in self_types:
            for val_t in val_types:
                self_t.append(val_t)

        return {self.builtins().none()}

class ListExtendMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="extend",
            pos_args=["self", "iterable"]
        )

    def adjusted_call(self, args):
        self.check_pos_args(args)

        self_types, iterable_types = args.pos_args()

        for self_t in self_types:
            for iterable_t in iterable_types:
                self_t.extend(iterable_t)

        return {self.builtins().none()}

class ListIterMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name=self.ITER_METHOD,
            pos_args=["self"]
        )

    def adjusted_call(self, args):
        self.check_pos_args(args)
        results = set()
        self_types = args.pos_args()[0]

        for self_t in self_types:
            results |= self_t.contents()

        return {self.builtins().generator().instance(yields=results)}


class ListInsertMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="insert",
            pos_args=["self", "i", "x"]
        )

    def adjusted_call(self, args):
        self.check_pos_args(args)
        self_types, i_types, x_types = args.pos_args()

        for self_t in self_types:
            for i_t in i_types:
                if not i_t.is_type(self.builtins().int()):
                    raise IntegerInterpetationError(i_t)
                for x_t in x_types:
                    self_t.append(x_t)

        return {self.builtins().int()}


class ListRemoveMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="remove",
            pos_args=["self", "x"]
        )

    def adjusted_call(self, args):
        return {self.builtins().none()}


class ListPopMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="pop",
            pos_args=["self"],
            keywords=["i"],
            keyword_defaults=[{self.builtins().int()}],
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
    def __init__(self):
        super().__init__(
            defined_name="clear",
            pos_args=["self"]
        )

    def adjusted_call(self, args):
        self.check_pos_args(args)
        return {self.builtins().none()}


class ListIndexMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="index",
            pos_args=["self", "x"],
            keywords=["start", "end"],
            keyword_defaults=[{self.builtins().int()}, {self.builtins().int()}]
        )

    def returns(self):
        self_types = self.env().lookup("self")
        results = set()
        for self_t in self_types:
            results |= self_t.contents()
        return results


class ListSortMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="sort",
            pos_args=["self"],
            keywords=["key", "reverse"],
            keyword_defaults=[{self.builtins().none()}, {self.builtins().bool()}]
        )

    def returns(self):
        return {self.builtins().none()}


class ListReverseMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="reverse",
            pos_args=["self"]
        )

    def returns(self):
        return {self.builtins().none()}


class ListCopyMethod(FunctionType):
    def __init__(self):
        super().__init__(
            defined_name="copy",
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
            )
        )

    #def instance(self, *args, **kwargs):
    #    return ListType(parents=[self], *args, **kwargs)

    def from_list(self, lst):
        contents = set()
        for types in lst:
            contents |= types
        return self.instance(init_contents=contents)

    #def merge_lists(self, *lsts):
    #    contents = set()
    #    for lst in lsts:
    #        contents |= lst.contents()
    #    return self.from_list([contents])


def create_list_class(builtins):
    from function_type import FunctionType

    cls = ListClass(builtins)



    cls.set_attr(cls.ADD_METHOD, {ListAddMethod()})
    cls.set_attr(cls.ITER_METHOD, {ListIterMethod()})
    cls.set_attr("append", {ListAppendMethod()})
    cls.set_attr("extend", {ListExtendMethod()})
    cls.set_attr("insert", {ListInsertMethod()})
    cls.set_attr("remove", {ListRemoveMethod()})
    cls.set_attr("pop", {ListPopMethod()})
    cls.set_attr("clear", {ListClearMethod()})
    cls.set_attr("index", {ListIndexMethod()})
    cls.set_attr("sort", {ListSortMethod()})
    cls.set_attr("reverse", {ListReverseMethod()})
    cls.set_attr("copy", {ListCopyMethod()})

    return cls
