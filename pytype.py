class PyType:
    NEW_METHOD = "__new__"
    INIT_METHOD = "__init__"
    DEL_METHOD = "__del__"
    REPR_METHOD = "__repr__"
    STR_METHOD = "__str__"
    BYTES_METHOD = "__bytes__"
    FORMAT_METHOD = "__format__"

    LT_METHOD = "__lt__"
    LE_METHOD = "__le__"
    EQ_METHOD = "__eq__"
    NE_METHOD = "__ne__"
    GT_METHOD = "__gt__"
    GE_METHOD = "__ge__"

    HASH_METHOD = "__hash__"
    BOOL_METHOD = "__bool__"

    GETATTR_METHOD = "__getattr__"
    GETATTRIBUTE_METHOD = "__getattribute__"
    SETATTR_METHOD = "__setattr__"
    DELATTR_METHOD = "__delattr__"
    DIR_METHOD = "__dir__"

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
        """
        The name of this type. This is equivalent to the result
        of obj.__class__.
        """
        return self.__name

    def attrs(self):
        """
        Returns:
            dict[str, set[PyType]]
        """
        return self.__attrs

    def has_attr(self, attr):
        return attr in self.__attrs

    """
    Wrappers for magic methods that affect this pytype.
    """

    def set_attr(self, attr, types):
        assert isinstance(types, set)
        assert all(isinstance(x, PyType) for x in types)

        if self.has_attr(attr):
            self.__attrs[attr] |= types
        else:
            self.__attrs[attr] = set(types)

    def get_attr(self, attr):
        if self.has_attr(attr):
            return self.__attrs[attr]
        else:
            raise KeyError("Attribute '{}' not in pytype '{}'".format(attr, self.name()))

    def call_attr(self, attr, args):
        """
        Call an attribute of this type. The result is the set of all results of
        calling each type that an attribute can be.

        Equivalent to: x.attr(args)

        Returns:
            set[PyType]
        """
        types = set()
        for t in self.get_attr(attr):
            types |= t.call(args)
        return types

    def _call_and_check_return(self, attr, expected, args):
        """
        Call an attribute and check that it returns an expected type. This is
        for methods like __hash__ or __str__ which must return specifically
        strs and ints otherwise a TypeError is raised.

        Args:
            attr (str)
            expected (PyType)
            args (arguments.Arguments)

        Returns:
            set[PyType]
        """
        if self.has_attr(attr):
            results = self.call_attr(attr, args)
            if results != {expected}:
                raise TypeError("{} for type '{}' returned non-{} (type {})".format(attr, self.name(), expected.name(), results))
        return {expected}

    def _optional_call(self, attr, default, args):
        """
        Call an attribute if it exists and return the results. Otherwise,
        return the default.

        Args:
            attr (str)
            default (PyType)
            args (arguments.Arguments)

        Returns:
            set[PyType]
        """
        if self.has_attr(attr):
            return self.call_attr(attr, args)
        else:
            return {default}

    """
    Implementations of magic methods
    http://www.diveintopython3.net/special-method-names.html

    These methods are ment to be used internally by this package and do not
    interact with the nodes returned by the python ast module. These methods
    handle only internal pytypes and should not accept or return ast nodes.
    """

    def call(self, args):
        """
        This emulates as if a variable was called in python space. This is for
        types that act like functions.

        Equivalent to: x(args) or x.__call__(args)

        Returns:
            set[PyType]
        """
        raise RuntimeError("pytype '{}' is not callable".format(self.name()))

    def call_new(self, args):
        """
        Called once when a class is defined.
        """
        from none_type import NONE_CLASS
        return self._optional_call(self.NEW_METHOD, NONE_CLASS.instance(), args)

    def call_init(self, args):
        """
        Only call this method if it is defined. Otherwise is does nothing.
        """
        from none_type import NONE_CLASS
        return self._optional_call(self.INIT_METHOD, NONE_CLASS.instance(), args)

    def call_del(self, args):
        return self.call_attr(self.DEL_METHOD, args)

    """
    These methods must return specific types. If they are custom implemented
    and do not return their specific types, a TypeError is raised at runtime.
    """

    def call_repr(self, args):
        from str_type import STR_CLASS
        return self._call_and_check_return(self.REPR_METHOD, STR_CLASS.instance(), args)

    def call_str(self, args):
        from str_type import STR_CLASS
        return self._call_and_check_return(self.STR_METHOD, STR_CLASS.instance(), args)

    def call_bytes(self, args):
        from bytes_type import BYTES_CLASS
        return self._call_and_check_return(self.BYTES_METHOD, BYTES_CLASS.instance(), args)

    def call_format(self, args):
        """
        This is what is called when performing a string format.

        Example at https://pyformat.info/#custom_1
        """
        from str_type import STR_CLASS
        return self._call_and_check_return(self.FORMAT_METHOD, STR_CLASS.instance(), args)

    """
    Rich comparison methods

    Only __eq__ and __ne__ are implemented by default where __eq__ compares the
    hash's of both objects and __ne__ is the inverse of the result of __eq__.
    """

    def call_lt(self, args):
        return self.call_attr(self.LT_METHOD, args)

    def call_le(self, args):
        return self.call_attr(self.LE_METHOD, args)

    def call_eq(self, args):
        from bool_type import BOOL_CLASS
        return self._optional_call(self.EQ_METHOD, BOOL_CLASS.instance(), args)

    def call_ne(self, args):
        from bool_type import BOOL_CLASS
        return self._optional_call(self.NE_METHOD, BOOL_CLASS.instance(), args)

    def call_gt(self, args):
        return self.call_attr(self.GT_METHOD, args)

    def call_ge(self, args):
        return self.call_attr(self.GE_METHOD, args)

    def call_hash(self, args):
        from int_type import INT_CLASS
        return self._call_and_check_return(self.HASH_METHOD, INT_CLASS.instance(), args)

    def call_bool(self, args):
        from bool_type import BOOL_CLASS
        return self._call_and_check_return(self.BOOL_METHOD, BOOL_CLASS.instance(), args)

    """
    Attribute access
    """

    def call_getattr(self, args):
        """
        This method is a wrapper for calling x.__getattr__. Ideally, this
        method will not actually be called explicitly by this package since
        the get_attr() method will be called instead. This method will
        really only be called when the __getattr__ method is explicitly called
        by the python program.
        """
        raise NotImplementedError("TODO: Implement logic for handling __getattr__")

    def call_getattribute(self, args):
        """
        This method is the uncoditional call for x.attr.
        """
        raise NotImplementedError("TODO: Implement logic for handling __getattribute__")

    def call_setattr(self, args):
        raise NotImplementedError("TODO: Implement logic for handling __setattr__")

    def call_delattr(self, args):
        return self.call_attr(self.DELATTR_METHOD, args)

    def call_dir(self, args):
        from tuple_type import TUPLE_CLASS
        return self._call_and_check_return(self.DIR_METHOD, TUPLE_CLASS.instance().new_container(), args)

    def call_getitem(self, args):
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
