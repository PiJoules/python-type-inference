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
    CONTAINS_METHOD = "__contains__"

    NEXT_METHOD = "__next__"
    ITER_METHOD = "__iter__"

    ADD_METHOD = "__add__"
    SUB_METHOD = "__sub__"
    MUL_METHOD = "__mul__"
    TRUEDIV_METHOD = "__truediv__"

    IADD_METHOD = "__iadd__"

    def __init__(self, name, init_attrs=None, parents=None):
        """
        Args:
            name (str)
            init_attrs (Optional[dict[str, set[PyType]]])
            parents (Optional[list[PyType]])
        """
        assert isinstance(name, str)

        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[PyType]]
        self.__parents = parents or []

    def parents(self):
        return self.__parents

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
        attrs = {}

        for parent in self.parents():
            for attr, types in parent.attrs().items():
                if attr in attrs:
                    attrs[attr] |= types
                else:
                    attrs[attr] = set(types)

        for attr, types in self.__attrs.items():
            if attr in attrs:
                attrs[attr] |= types
            else:
                attrs[attr] = set(types)

        return attrs

    def has_attr(self, attr):
        return attr in self.attrs()

    def exclusive_has_attr(self, attr):
        return attr in self.__attrs

    def is_type(self, other):
        """
        Args:
            other (class_type.ClassType)
        """
        if self.name() == other.name():
            return True

        for parent in self.parents():
            if parent.is_type(other):
                return True

        return False

    """
    Wrappers for magic methods that affect this pytype.
    """

    def set_attr(self, attr, types):
        assert isinstance(types, set)
        assert all(isinstance(x, PyType) for x in types)

        if self.exclusive_has_attr(attr):
            self.__attrs[attr] |= types
        else:
            self.__attrs[attr] = set(types)

    def get_attr(self, attr):
        if self.has_attr(attr):
            return self.attrs()[attr]
        else:
            from class_type import ClassType
            if isinstance(self, ClassType):
                raise KeyError("Attribute '{}' not in class '{}'".format(attr, self.defined_name()))
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
        attrs = self.get_attr(attr)
        for t in attrs:
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
        from builtin_types import NONE_TYPE
        return self._optional_call(self.NEW_METHOD, NONE_TYPE, args)

    def call_init(self, args):
        """
        Only call this method if it is defined. Otherwise is does nothing.
        """
        from builtin_types import NONE_TYPE
        return self._optional_call(self.INIT_METHOD, NONE_TYPE, args)

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
        from builtin_types import BOOL_TYPE
        return self._optional_call(self.EQ_METHOD, BOOL_TYPE, args)

    def call_ne(self, args):
        from builtin_types import BOOL_TYPE
        return self._optional_call(self.NE_METHOD, BOOL_TYPE, args)

    def call_gt(self, args):
        return self.call_attr(self.GT_METHOD, args)

    def call_ge(self, args):
        return self.call_attr(self.GE_METHOD, args)

    def call_hash(self, args):
        from builtin_types import INT_TYPE
        return self._call_and_check_return(self.HASH_METHOD, INT_TYPE, args)

    def call_bool(self, args):
        from builtin_types import BOOL_TYPE
        return self._call_and_check_return(self.BOOL_METHOD, BOOL_TYPE, args)

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

    """
    Emulating container types
    """

    def call_getitem(self, args):
        return self.call_attr(self.GETITEM_METHOD, args)

    def call_contains(self, args):
        return self.call_attr(self.CONTAINS_METHOD, args)

    """
    Emulating numeric types
    """

    def _alt_method(self, alt, method):
        """Get an alternated method."""
        assert method.startswith("__")
        assert method.endswith("__")
        return "__" + alt + method[2:-2] + "__"

    def _rmethod(self, method):
        """Get the reflected method."""
        return self._alt_method("r", method)

    def _imethod(self, method):
        """Get the augmented (inplace) method."""
        return self._alt_method("i", method)

    def _call_numeric_op(self, method, args, aug=False):
        from arguments import Arguments

        if aug:
            i_meth = self._imethod(method)
            return self.call_attr(i_meth, args)

        if self.has_attr(method):
            return self.call_attr(method, args)
        else:
            # Get the reflected magic method
            r_meth = self._rmethod(method)

            # Get the right side typs
            pos_args = args.pos_args()
            if len(pos_args) != 1:
                raise RuntimeError("Expected 1 argument for numeric operation")
            right_types = pos_args.pop()

            results = set()
            for t in right_types:
                if t.has_attr(r_meth):
                    results |= t.call_attr(r_meth, Arguments([self]))
                else:
                    raise RuntimeError("No support for {} or {} on types '{}' and '{}'".format(method, r_meth, self, t))
            return results

    def call_add(self, args, **kwargs):
        return self._call_numeric_op(self.ADD_METHOD, args, **kwargs)

    def call_sub(self, args, **kwargs):
        return self._call_numeric_op(self.SUB_METHOD, args, **kwargs)

    def call_mul(self, args, **kwargs):
        return self._call_numeric_op(self.MUL_METHOD, args, **kwargs)

    def call_truediv(self, args, **kwargs):
        return self._call_numeric_op(self.TRUEDIV_METHOD, args, **kwargs)

    """
    Iterator types
    """

    def call_iter(self, args):
        return self.call_attr(self.ITER_METHOD, args)

    def call_next(self, args):
        return self.call_attr(self.NEXT_METHOD, args)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        raise NotImplementedError("Must implement __eq__ for pytype '{}'".format(type(self)))

    def __str__(self):
        return self.name()


def load_buultin_constants():
    from builtin_types import STR_TYPE
    return {
        "__name__": {STR_TYPE},
    }


def load_builtin_vars():
    from function_type import BuiltinFunction
    from instance_type import InstanceType
    from tuple_type import TUPLE_CLASS
    from dict_type import DICT_CLASS
    from builtin_types import (
        INT_CLASS, FLOAT_CLASS, BOOL_CLASS, STR_CLASS, FILE_CLASS,
        NONE_TYPE, INT_TYPE, FILE_TYPE, BOOL_TYPE, STR_TYPE
    )

    from value_error_type import VALUE_ERROR_CLASS


    """
    Builtin functions
    """
    class PrintFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                "print",
                vararg="objects",
                kwonlyargs=["sep", "end", "file", "flush"],
                kwonly_defaults=[
                    {STR_TYPE},
                    {STR_TYPE},
                    {FILE_TYPE},
                    {BOOL_TYPE},
                ]
            )

        def call(self, args):
            return {NONE_TYPE}
    print_func = PrintFunction()


    class InputFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                "input",
                keywords=["prompt"],
                keyword_defaults=[{STR_TYPE}],
            )
        def call(self, args):
            return {STR_TYPE}
    input_func = InputFunction()

    builtins = {
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
    builtins.update(load_buultin_constants())

    return builtins

