from instance_type import InstanceType
from class_type import ClassType
from pytype import PyType
from arguments import empty_args
from generator_type import GENERATOR_CLASS
from int_type import INT_CLASS
from bool_type import BOOL_CLASS


class IntegerInterpetationError(TypeError):
    def __init__(self, t):
        super().__init__("'{}' object cannot be interpretted as an integer".format(t))


LIST_NAME = "list"


class ListType(InstanceType):
    def __init__(self, init_contents=None, *args, **kwargs):
        super().__init__(LIST_NAME, *args, **kwargs)

        # Combine all contents into one set. Order will not matter for
        # indexing lists.
        init_contents = init_contents or []
        assert isinstance(init_contents, list)
        for types in init_contents:
            assert isinstance(types, set)
            assert all(isinstance(x, PyType) for x in types)

        contents = set()
        for types in init_contents:
            contents |= types
        self.__contents = contents

    def append(self, item):
        assert isinstance(item, PyType)
        self.__contents.add(item)

    def extend(self, iterable_t):
        for iter_t in iterable_t.call_iter(empty_args()):
            self.__contents |= iter_t.call_next(empty_args())

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


class ListClass(ClassType):
    def __init__(self, *args, **kwargs):
        super().__init__(
            defined_name=LIST_NAME,
            *args, **kwargs
        )

    def instance(self, *args, **kwargs):
        return ListType(parents=[self], *args, **kwargs)

    def inst_from_list(self, lst):
        return self.instance(init_contents=[lst.contents()])

    def merge_lists(self, *lsts):
        contents = set()
        for lst in lsts:
            contents |= lst.contents()
        return self.instance(
            init_contents=[contents]
        )


def create_class():
    from int_type import INT_CLASS
    from slice_type import SLICE_CLASS
    from none_type import NONE_CLASS
    from function_type import BuiltinFunction
    from getitem_method import GetItemMethod
    from add_method import AddMethod

    cls = ListClass()

    class ListGetItemMethod(GetItemMethod):
        def adjusted_call(self, args):
            self.check_pos_args(args)

            results = set()
            self_types, key_types = args.pos_args()

            for self_t in self_types:
                for key_t in key_types:
                    if key_t.is_type(INT_CLASS.instance()):
                        # Accessing 1 item in the tuple
                        results |= self_t.contents()
                    elif key_t.is_type(SLICE_CLASS.instance()):
                        results.add(cls.inst_from_list(self_t))
                    else:
                        raise RuntimeError("Unable to index {} with key {}".format(self_t, key_t))

            return results

    class ListAddMethod(AddMethod):
        def adjusted_call(self, args):
            self.check_pos_args(args)

            results = set()
            self_types, other_types = args.pos_args()

            for self_t in self_types:
                for other_t in other_types:
                    if other_t.is_type(cls.instance()):
                        results.add(cls.merge_lists(self_t, other_t))
                    else:
                        raise RuntimeError("Unable to concatenate list with {}".format(other_t))

            return results

    class ListAppendMethod(BuiltinFunction):
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

            return {NONE_CLASS.instance()}

    class ListExtendMethod(BuiltinFunction):
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

            return {NONE_CLASS.instance()}

    class ListIterMethod(BuiltinFunction):
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

            return {GENERATOR_CLASS.instance(yields=results)}


    class ListInsertMethod(BuiltinFunction):
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
                    if not i_t.is_type(INT_CLASS.instance()):
                        raise IntegerInterpetationError(i_t)
                    for x_t in x_types:
                        self_t.append(x_t)

            return {NONE_CLASS.instance()}


    class ListRemoveMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="remove",
                pos_args=["self", "x"]
            )

        def adjusted_call(self, args):
            return {NONE_CLASS.instance()}


    class ListPopMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="pop",
                pos_args=["self"],
                keywords=["i"],
                keyword_defaults=[{INT_CLASS.instance()}],
            )

        def returns(self):
            env = self.env()
            self_types = env.lookup("self")
            i_types = env.lookup("i")

            results = set()

            for self_t in self_types:
                for i_t in i_types:
                    if not i_t.is_type(INT_CLASS.instance()):
                        raise IntegerInterpetationError(i_t)
                    else:
                        results |= self_t.contents()

            return results

    class ListClearMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="clear",
                pos_args=["self"]
            )

        def adjusted_call(self, args):
            self.check_pos_args(args)
            return {NONE_CLASS.instance()}


    class ListIndexMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="index",
                pos_args=["self", "x"],
                keywords=["start", "end"],
                keyword_defaults=[{INT_CLASS.instance()}, {INT_CLASS.instance()}]
            )

        def returns(self):
            self_types = self.env().lookup("self")
            results = set()
            for self_t in self_types:
                results |= self_t.contents()
            return results


    class ListSortMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="sort",
                pos_args=["self"],
                keywords=["key", "reverse"],
                keyword_defaults=[{NONE_CLASS.instance()}, {BOOL_CLASS.instance()}]
            )

        def returns(self):
            return {NONE_CLASS.instance()}


    class ListReverseMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name="reverse",
                pos_args=["self"]
            )

        def returns(self):
            return {NONE_CLASS.instance()}


    cls.set_attr(cls.GETITEM_METHOD, {ListGetItemMethod()})
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

    return cls


LIST_CLASS = create_class()
