import ast

import inference
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

    def _update_positional_args(self, args):
        """
        Returns:
            set[str]: Arguments defined as positional args
        """
        defined_args = set()
        pos_args = args.pos_args()
        for i, arg in enumerate(self.__pos_args):
            self.__env.bind(arg, pos_args[i])
            defined_args.add(arg)
        return defined_args

    def _update_keyword_args(self, args, defined_args):
        # Make sure the positional args are fully exhausted first
        pos_args = args.pos_args()
        kw_args = args.keyword_args()
        for i, arg in enumerate(self.__keywords):
            if len(pos_args) > len(defined_args):
                self.__env.bind(arg, pos_args[len(defined_args)])
                defined_args.add(arg)
            else:
                self.__env.bind(arg, kw_args.get(arg, self.__keyword_defaults[i]))
        return defined_args

    def _update_vararg(self, args, counted_pos_args):
        """
        Args:
            args (arguments.Arguments)
            counted_pos_args (int): Number of arguments unpacked into positional
                and keyword arguments.
        """
        pos_args = args.pos_args()
        tup = self.__env.lookup_type("tuple").new_container(
            init_contents=tuple(pos_args[counted_pos_args:]))
        self.__env.bind(self.__vararg, {tup})

    def _update_kwonly_args(self, args):
        kw_args = args.keyword_args()
        for i, arg in enumerate(self.__kwonlyargs):
            self.__env.bind(arg, kw_args.get(arg, self.__kwonly_defaults[i]))

    def _update_kwargs(self, args):
        """
        All keyowrds provided in the arguments but not in the keyword/kwonly
        args go here.
        """
        value_types = set()
        expected_keywords = set(self.__keywords + self.__kwonlyargs)
        for arg, types in args.keyword_args().items():
            if arg not in expected_keywords:
                value_types |= types

        # Create new dict container
        d = self.__env.lookup_type("dict").new_container(
            key_types={self.__env.lookup_type("str")},
            value_types=value_types,
        )
        self.__env.bind(self.__kwarg, {d})

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
        env = self.__env
        defined_args = set()

        # Positional args
        defined_args = self._update_positional_args(args)

        # Keyword args
        # Make sure the positional args are fully exhausted first
        defined_args = self._update_keyword_args(args, defined_args)

        # Vararg
        if self.__vararg:
            self._update_vararg(args, len(defined_args))
        elif len(args.pos_args()) > len(defined_args):
            # There are still extra positonal arguments, but not vararg given
            raise RuntimeError("Too many arguments provided for function")

        if args.vararg() or args.kwarg():
            raise NotImplementedError

        # Keyword only args
        self._update_kwonly_args(args)

        # Kwarg
        if self.__kwarg:
            self._update_kwargs(args)
        elif len(args.keyword_args()) > len(self.__keywords + self.__kwonlyargs):
            raise RuntimeError("Too many keyword arguments provided for function")

    def returns(self):
        """
        Find the return types of this function.
        """
        returns = set()

        stack = list(self.__ref_node.body)
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

        return returns or {self.__env.lookup_type("None")}

    def call_and_update(self, args):
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
        env = inference.Environment(parent_env=parent_env)

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


class BuiltinFunction(FunctionType):
    def call_and_update(self, args):
        raise NotImplementedError

