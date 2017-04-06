import ast
import pytype


class FunctionType(pytype.PyType):
    """
    Type that can contain code to be executed.
    """
    def __init__(self, env, node, *args, pos_args=None, keywords=None,
                 vararg=None, kwonlyargs=None, kwarg=None,
                 keyword_defaults=None, kwonly_defaults=None,
                 defined_name=None,
                 **kwargs):
        """
        Args:
            name (str)
            env (inference.Environment)
            node (ast.FunctionDef)
            args (tuple)
            pos_args (Optional[list[str]])
            keywords (Optional[list[str]])  # List to retain positional args unpacked into keyword args
            vararg (Optional[str])
            kwonlyargs (Optional[list[str]])
            kwarg (Optional[str])
            kwargs (dict)
            keyword_defaults (Optional[list[set[pytype.PyType]]])
            kwonly_defaults (Optional[list[set[pytype.PyType]]])
            defined_name (Optional[str]): The name that comes with the definition of a function.
                If the function is created dynamically at runtime, this may be None.
        """
        from environment import Environment
        super().__init__("function", *args, **kwargs)
        self.__ref_node = node

        if defined_name:
            self.__defined_name = defined_name
        elif node:
            self.__defined_name = node.name
        else:
            self.__defined_name = None
        self.__env = env or Environment(self.__defined_name)

        self.__pos_args = pos_args or []
        self.__keywords = keywords or []
        self.__vararg = vararg
        self.__kwonlyargs = kwonlyargs or []
        self.__kwarg = kwarg

        self.__keyword_defaults = keyword_defaults or []
        self.__kwonly_defaults = kwonly_defaults or []
        self.__owner = None

        # Type checks
        assert len(self.__keywords) == len(self.__keyword_defaults)
        assert len(self.__kwonlyargs) == len(self.__kwonly_defaults)

        assert all(isinstance(x, set) for x in self.__keyword_defaults)
        for default in self.__keyword_defaults:
            assert all(isinstance(x, pytype.PyType) for x in default)
        assert all(isinstance(x, set) for x in self.__kwonly_defaults)
        for default in self.__kwonly_defaults:
            assert all(isinstance(x, pytype.PyType) for x in default)


    """
    Getters
    """

    def defined_name(self):
        return self.__defined_name

    def pos_args(self):
        return self.__pos_args

    def keywords(self):
        return self.__keywords

    def vararg(self):
        return self.__vararg

    def kwonlyargs(self):
        return self.__kwonlyargs

    def kwarg(self):
        return self.__kwarg

    def keyword_defaults(self):
        return self.__keyword_defaults

    def kwonly_defaults(self):
        return self.__kwonly_defaults

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def update_env(self, args):
        """
        Update this env based on the arguments provided.

        This also handles unpacking.

        Example:
        def func(a, b=1, c=2, *d, e=3, **f):
            ...

        func(1, 2, c=3, e=5) -> a = 1, b = 2, c=3, e=5
        func(1,2,3,4,5) -> a=1,b=2,c=3,d=(4,5)
        """
        args.unpack_positional_args(self)
        args.unpack_keyword_args(self)
        if self.vararg():
            args.unpack_vararg(self)
        args.unpack_kwonly_args(self)
        if self.kwarg():
            args.unpack_kwargs(self)

        # Ensure the arguments are exhausted
        if args:
            raise RuntimeError("""Arguments for call to function '{}' were not fully exhausted.
Expected {} positional arguments, {} keyword arguments, {} variable positional argument,
and {} variable keyword argument.
{} positional arguments, {} keyword arguments, {} variable positional argument,
and {} variable keyword argument were left unhandled.
""".format(self.defined_name(),
           len(self.pos_args()),
           len(self.keywords()) + len(self.kwonlyargs()),
           "1" if self.vararg() else "no",
           "1" if self.kwarg() else "no",
           len(args.pos_args()),
           len(args.keyword_args()),
           "1" if args.vararg() else "no",
           "1" if args.kwarg() else "no",
           ))

    def returns(self):
        """
        Returns all values returned and yielded
        by this function.

        TODO: Update to perhaps include yieldfrom and raise

        Returns:
            set[PyType] x3: Return types and yielded types.
        """
        from builtin_types import NONE_TYPE

        self.env().parse_sequence(self.__ref_node.body)
        returns = self.env().returns()
        yields = self.env().yields()

        # Empty returns means return None
        returns = returns or {NONE_TYPE}
        if yields:
            from generator_type import GENERATOR_CLASS
            return {GENERATOR_CLASS.instance(
                yields=yields,
                returns=returns
            )}
        else:
            return returns

    def adjusted_call(self, args):
        """
        The args passed to this method are adjusted to include self as the
        first positional argument if called by an instance.
        """
        print(self.env().variables())
        self.update_env(args)
        print(self.env().variables())
        return self.returns()

    def call(self, args):
        """
        Call this function, update its environment based on the arguments,
        and return possible return types of this function.
        """
        print(args)
        if self.is_bound_method():
            args.prepend_owner(self.owner())

        results = self.adjusted_call(args)

        if self.is_bound_method():
            self.unbind_method()
        return results

    def env(self):
        return self.__env

    @classmethod
    def from_node_and_env(cls, node, parent_env):
        """
        TODO: Handle remaining properties

        Args:
            node (ast.FunctionDef)
            parent_env (inference.Environment)
        """
        from environment import Environment

        env = Environment(node.name, parent_env=parent_env)

        # Add the arguments as variables
        env.parse_arguments(node.args)

        # Save arguments
        pos_args = []
        keywords = []
        keyword_defaults = []
        vararg = None
        kwonlyargs = []
        kwonly_defaults = []
        kwarg = None

        args_node = node.args

        # Positional
        pos_arg_nodes = args_node.args
        pos_end = len(pos_arg_nodes) - len(args_node.defaults)
        for arg in pos_arg_nodes[:pos_end]:
            pos_args.append(arg.arg)

        # Keywords
        for i, arg in enumerate(pos_arg_nodes[pos_end:]):
            keywords.append(arg.arg)
            keyword_defaults.append(parent_env.eval(args_node.defaults[i]))

        # Vararg
        if args_node.vararg:
            vararg = args_node.vararg.arg

        # Kwonlyargs
        for i, arg in enumerate(args_node.kwonlyargs):
            kwonlyargs.append(arg.arg)
            kw_def = args_node.kw_defaults[i]  # The kw_def can be None
            if kw_def is None:
                kwonly_defaults.append(set())
            else:
                kwonly_defaults.append(parent_env.eval(kw_def))

        # Kwarg
        if args_node.kwarg:
            kwarg = args_node.kwarg.arg

        func = cls(env, node,
                   pos_args=pos_args,
                   keywords=keywords,
                   vararg=vararg,
                   kwonlyargs=kwonlyargs,
                   kwarg=kwarg,
                   keyword_defaults=keyword_defaults,
                   kwonly_defaults=kwonly_defaults)
        return func

    def ref_node(self):
        return self.__ref_node

    def bind_method(self, owner):
        from instance_type import InstanceType
        assert isinstance(owner, InstanceType)
        self.__owner = owner

    def unbind_method(self):
        self.__owner = None

    def is_bound_method(self):
        return self.__owner is not None

    def owner(self):
        return self.__owner


class BuiltinFunction(FunctionType):
    def __init__(self, defined_name, *args, **kwargs):
        super().__init__(None, None, *args, defined_name=defined_name, **kwargs)

    def returns(self):
        raise NotImplementedError

    def check_pos_args(self, args):
        """
        Assert the number of positional arguments provided matches the number
        provided.
        """
        if not self.vararg():
            pos_provided = len(args.pos_args())
            pos_defined = len(self.pos_args())
            if pos_provided != pos_defined:
                raise RuntimeError("""
Function '{}' accepts {} positional arguments. {} were provided.
Defined positional args: {}
Provided args: {}
"""
.format(
    self.defined_name(),
    pos_defined,
    pos_provided,
    self.pos_args(),
    args.pos_args(),
))

    def check_keyword_args(self, args):
        if not self.kwarg():
            kwarg_provided = len(args.keyword_args())
            kwarg_defined = len(self.keywords()) + len(self.kwonlyargs())
            if kwarg_provided != kwarg_defined:
                raise RuntimeError("Function '{}' accepts {} keyword arguments. {} were provided.".format(self.defined_name(), kwarg_defined, kwarg_provided))


