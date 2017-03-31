import sys
import ast


class Arguments:
    """
    Intermediate class for representing arguments passed to some callable object.

    Note: The Call ast node does not support a way do tell the difference between
    keyword and keyword only arguments. So a function defined as:

    def func(a, b=1, *c, d=2, **e):
        ...

    A function call like:

    func(a, b=1, *c, d=2, **e)

    looks exactly like

    func(a, b=1, d=2, *c, **e)

    when represented as asts. The Call node only has fields for args and keywords,
    so the ast combines keywords and keyword only args into the same field.
    """

    def __init__(self, pos_args=None, keyword_args=None, vararg=None, kwarg=None):
        """
        Args:
            pos_args (Optional[list[set[pytype.PyType]]])
            keyword_args (Optional[dict[str, set[pytype.PyType]][])
            vararg (Optional[pytype.PyType])
            kwarg (Optional[pytype.PyType])
        """
        from tuple_type import TUPLE_CLASS
        from dict_type import DICT_CLASS
        from str_type import STR_CLASS

        self.__pos_args = pos_args or []
        self.__keyword_args = keyword_args or {}
        self.__vararg = vararg or TUPLE_CLASS.instance()
        self.__kwarg = kwarg or DICT_CLASS.instance()

        # Type checks
        assert isinstance(self.__pos_args, list)
        assert all(isinstance(x, set) for x in self.__pos_args)

        assert isinstance(self.__keyword_args, dict)
        assert all(isinstance(x, set) for x in self.__pos_args)

        assert isinstance(self.__vararg, type(TUPLE_CLASS.instance()))
        assert isinstance(self.__kwarg, type(DICT_CLASS.instance()))
        for types in self.__kwarg.key_types():
            assert isinstance(types, set)
            assert all(x == STR_CLASS.instance() for x in types)

    def pos_args(self):
        return self.__pos_args

    def vararg(self):
        return self.__vararg

    def keyword_args(self):
        return self.__keyword_args

    def kwarg(self):
        return self.__kwarg

    def __bool__(self):
        """True if contains any arguments."""
        return bool(self.pos_args() or
                    self.keyword_args() or
                    self.vararg() or
                    self.kwarg())

    @classmethod
    def from_call_node_v3_4_older(cls, node, ref_env):
        raise NotImplementedError("Implement logic for evaluating calls in v3.4 or older")

    @classmethod
    def from_call_node_v3_5_newer(cls, node, ref_env):
        pos_args = []
        vararg = None
        keyword_args = {}
        kwarg = None

        arg_nodes = node.args
        for pos_node in arg_nodes:
            if isinstance(pos_node, ast.Starred):
                # Vararg
                vararg = ref_env.eval(pos_node.value)
            else:
                # Posarg
                pos_args.append(ref_env.eval(pos_node))

        keyword_nodes = node.keywords
        for kw_node in keyword_nodes:
            arg = kw_node.arg
            val = kw_node.value
            if arg:
                # Keyword arg
                keyword_args[arg] = ref_env.eval(val)
            else:
                # Kwargs
                kwarg = ref_env.eval(val)

        return cls(pos_args, keyword_args, vararg=vararg, kwarg=kwarg)

    @classmethod
    def from_call_node(cls, node, ref_env):
        """
        The AST for call is different between python 3.4 and 3.5.
        """
        info = sys.version_info
        if info[0] >= 3 and info[1] >= 5:
            return cls.from_call_node_v3_5_newer(node, ref_env)
        else:
            return cls.from_call_node_v3_4_older(node, ref_env)

        return cls(pos_args, vararg, keyword_args, kwarg)

    """
    Argument unpacking into function args. These functions mutate this
    arguments object by removing the pytypes held under the pos_args and
    keyword args.
    """

    def unpack_positional_args(self, func):
        """
        Binds this object's positional arguments to the arguments in the
        function's environment. This mutates the Arguments object by removing
        the positional arguments from this object to indicate it was already
        binded to a function arg.

        Args:
            func (function_type.FunctionType)
        """
        env = func.env()
        pos_args = self.pos_args()
        for i, arg in enumerate(func.pos_args()):
            env.bind(arg, pos_args.pop(0))

    def unpack_keyword_args(self, func):
        """
        Unpack any remaining positional args then use the rest for keywords.
        """
        env = func.env()
        kw_defs = func.keyword_defaults()
        pos_args = self.pos_args()
        kw_args = self.keyword_args()
        for i, arg in enumerate(func.keywords()):
            if pos_args:
                env.bind(arg, pos_args.pop(0))
            else:
                env.bind(arg, kw_args.pop(arg, kw_defs[i]))

    def unpack_vararg(self, func):
        """
        Add any remaining positional arguments then the unpacked vararg.
        """
        from tuple_type import TUPLE_CLASS

        pos_args = self.pos_args()
        tup = TUPLE_CLASS.instance().new_container(
            init_contents=tuple(pos_args) + self.vararg().contents()
        )
        func.env().bind(func.vararg(), {tup})
        self.__pos_args.clear()
        self.__vararg = TUPLE_CLASS.instance()

    def unpack_kwonly_args(self, func):
        kw_args = self.keyword_args()
        env = func.env()
        kwonlw_defs = func.kwonly_defaults()
        for i, arg in enumerate(func.kwonlyargs()):
            env.bind(arg, kw_args.pop(arg, kwonlw_defs[i]))

    def unpack_kwargs(self, func):
        from str_type import STR_CLASS
        from dict_type import DICT_CLASS

        value_types = set()
        for types in self.keyword_args().values():
            value_types |= types

        d = DICT_CLASS.instance().new_container(
            key_types={STR_CLASS.instance()},
            value_types=value_types | self.kwarg().value_types()
        )
        func.env().bind(func.kwarg(), {d})
        self.__keyword_args.clear()
        self.__kwarg = DICT_CLASS.instance()

    def prepend_owner(self, owner):
        """
        Adds 'self' as the first positional argument for a bounded method in
        an instance.

        Args:
            owner (instance_type.InstanceType)
        """
        self.__pos_args.insert(0, {owner})

    def __str__(self):
        return "{}, {}, {}, {}".format(
            [set(map(str, x)) for x in self.pos_args()],
            self.keyword_args(),
            self.vararg(),
            self.kwarg()
        )


EMPTY_ARGS = Arguments([], {})


