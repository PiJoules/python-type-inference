import ast
import pytype


class FunctionType(pytype.PyType):
    """
    Type that can contain code to be executed.
    """
    def __init__(self, env, node, *args, pos_args=None, keywords=None,
                 vararg=None, kwonlyargs=None, kwarg=None,
                 keyword_defaults=None, kwonly_defaults=None, **kwargs):
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
        """
        super().__init__("function", *args, **kwargs)
        self.__env = env  # inference.Environment
        self.__ref_node = node

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
        if self.__ref_node is None:
            return None
        return self.__ref_node.name

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

    def update_args(self, args):
        """
        Update this env based on the arguments provided.

        This also handles unpacking.

        Example:
        def func(a, b=1, c=2, *d, e=3, **f):
            ...

        func(1, 2, c=3, e=5) -> a = 1, b = 2, c=3, e=5
        func(1,2,3,4,5) -> a=1,b=2,c=3,d=(4,5)
        """
        if self.__owner:
            # For bound methods
            args.prepend_owner(self.__owner)
        args.unpack_positional_args(self)
        args.unpack_keyword_args(self)
        if self.vararg():
            args.unpack_vararg(self)
        args.unpack_kwonly_args(self)
        if self.kwarg():
            args.unpack_kwargs(self)

    def returns(self):
        """
        Find the return types of this function.
        """
        returns = set()

        stack = list(self.__ref_node.body)[::-1]
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                returns |= self.__env.eval(node.value)
            elif isinstance(node, (ast.If, ast.While)):
                stack += node.body + node.orelse
                # Evalate the test to check for function args
                self.__env.eval(node.test)
            elif isinstance(node, ast.For):
                stack += node.body + node.orelse
                self.__env.eval(node.iter)
            elif isinstance(node, ast.Try):
                stack += node.body + node.orelse + node.finalbody
                for handler in node.handlers:
                    stack += handler.body
            elif isinstance(node, ast.With):
                stack += node.body
                for item in node.items:
                    self.__env.eval(item.context_expr)
            else:
                # Parse everything else
                self.__env.parse(node)

        from none_type import NONE_CLASS
        return returns or {NONE_CLASS.instance()}

    def call(self, args):
        """
        Call this function, update its environment based on the arguments,
        and return possible return types of this function.
        """
        self.update_args(args)
        return self.returns()

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
        from inference import Environment

        env = Environment(parent_env=parent_env)

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

    def bind_owner(self, owner):
        self.__owner = owner


class BuiltinFunction(FunctionType):
    def __init__(self, *args, **kwargs):
        super().__init__(None, None, *args, **kwargs)

    def call(self, args):
        raise NotImplementedError

