class PyType:
    INIT_METHOD = "__init__"
    GETITEM_METHOD = "__getitem__"

    def __init__(self, name, init_attrs=None, parents=None):
        """
        Args:
            name (str)
            init_attrs (Optional[dict[str, set[PyType]]])
            parents (Optional[list[PyType]])
        """
        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[PyType]]
        self.__parents = parents or []

    def name(self):
        return self.__name

    def attrs(self):
        return self.__attrs

    def add_attr(self, attr, types):
        assert isinstance(types, set)
        assert all(isinstance(x, PyType) for x in types)

        if attr in self.__attrs:
            self.__attrs[attr] |= types
        else:
            self.__attrs[attr] = set(types)

    def get_attr(self, attr):
        if attr in self.__attrs:
            return self.__attrs[attr]
        else:
            raise KeyError("Attribute '{}' not in pytype '{}'".format(attr, self.defined_name()))

    def call(self, args):
        """
        Returns:
            set[PyType]
        """
        raise RuntimeError("pytype '{}' is not callable".format(self.name()))

    """
    Methods for calling specific functions owned by this type.
    """
    def call_attr(self, attr, args):
        types = set()
        for t in self.get_attr(attr):
            types |= t.call(args)
        return types

    def call_init(self, args=None):
        if self.INIT_METHOD in self.attrs():
            return self.call_attr(self.INIT_METHOD, args)
        else:
            return set()

    def call_getitem(self, args=None):
        return self.call_attr(self.GETITEM_METHOD, args)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        raise NotImplementedError("Must implement __hash__ for pytype '{}'".format(type(self)))

    def __eq__(self, other):
        raise NotImplementedError("Must implement __eq__ for pytype '{}'".format(type(self)))



def load_builtin_vars():
    from function_type import BuiltinFunction
    from class_type import BuiltinClass
    from instance_type import InstanceType
    from tuple_type import TUPLE_CLASS
    from dict_type import DICT_CLASS
    from float_type import FLOAT_CLASS
    from int_type import INT_CLASS
    from bool_type import BOOL_CLASS
    from none_type import NONE_CLASS
    from str_type import STR_CLASS
    from file_type import FILE_CLASS

    from value_error_type import VALUE_ERROR_CLASS


    """
    Builtin functions
    """
    class PrintFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                vararg="objects",
                kwonlyargs=["sep", "end", "file", "flush"],
                kwonly_defaults=[
                    {STR_CLASS.instance()},
                    {STR_CLASS.instance()},
                    {FILE_CLASS.instance()},
                    {BOOL_CLASS.instance()},
                ]
            )

        def call(self, args):
            return {NONE_CLASS.instance()}
    print_func = PrintFunction()


    class InputFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                keywords=["prompt"],
                keyword_defaults=[{STR_CLASS.instance()}],
            )
        def call(self, args):
            return {STR_CLASS.instance()}
    input_func = InputFunction()


    return {
        "int": {INT_CLASS},
        "float": {FLOAT_CLASS},
        "bool": {BOOL_CLASS},
        "str": {STR_CLASS},
        "tuple": {TUPLE_CLASS},
        "dict": {DICT_CLASS},
        "print": {print_func},
        "input": {input_func},

        "ValueError": {VALUE_ERROR_CLASS},
    }
