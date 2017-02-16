import ast
import inference


class PyType:
    def __init__(self, name, init_attrs=None, parents=None, owner=None):
        """
        Args:
            name (str)
            init_attrs (Optional[dict[str, set[PyType]]])
            parents (Optional[list[PyType]])
            owner (Optional[PyType])
        """
        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[PyType]]
        self.__parents = parents or []
        self.__owner = owner

    def name(self):
        return self.__name

    def __ne__(self, other):
        return not (self == other)


class FunctionType(PyType):
    """
    Type that can contain code to be executed.
    """
    def __init__(self, name, env, node, *args, pos_args=None, keywords=None,
                 vararg=None, kwonlyargs=None, kwarg=None, **kwargs):
        """
        Args:
            name (str)
            env (inference.Environment)
            node (ast.FunctionDef)
            args (tuple)
            pos_args (Optional[list[str]])
            keywords (Optional[list[str]])  # List to retain positional args unpacked into keyword args
            vararg (Optional[str])
            kwonlyargs (Optional[set[str]])
            kwarg (Optional[str])
            kwargs (dict)
        """
        super().__init__(name, *args, **kwargs)
        self.__env = env  # inference.Environment
        self.__ref_node = node

        self.__pos_args = pos_args or []
        self.__keywords = keywords or []
        self.__vararg = vararg
        self.__kwonlyargs = kwonlyargs or set()
        self.__kwarg = kwarg

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
        env = self.__env
        defined_args = set()

        # Positional args
        pos_args = args.pos_args()
        for i, arg in enumerate(self.__pos_args):
            env.bind(arg, pos_args[i])
            defined_args.add(arg)
        counted_pos_args = len(self.__pos_args)

        # Keyword args
        # Make sure the positional args are fully exhausted first
        for i, arg in enumerate(self.__keywords):
            if len(pos_args) > counted_pos_args:
                env.bind(arg, pos_args[counted_pos_args])
                defined_args.add(arg)
                counted_pos_args += 1

        # Vararg
        if len(pos_args) > counted_pos_args:
            if self.__vararg:
                # Create new tuple containing these types
                tup = self.__env.lookup_type("tuple").new_container()
                for types in pos_args[counted_pos_args:]:
                    tup.add_container_types(types)
                env.bind(self.__vararg, {tup})
            else:
                raise RuntimeError("Too many arguments provided for function '{}'".format(self.name()))

        ## Then fill in the remaining keyword arguments
        #kw_args = args.keyword_args()
        #for i in range(remaining, len(self.__keywords)):
        #    arg = self.__keywords[i]

        #    assert arg not in defined_args, "Multiple definitions of argument '{}' provided".format(arg)

        #    env.bind(arg, kw_args[arg])
        #    defined_args.add(arg)

        ## Vararg
        #vararg = args.vararg()
        #if vararg:
        #    env.bind(self.__vararg, vararg)
        #    defined_args.add(self.__vararg)

        ## Keyword only args
        #kwonlyargs = args.kwonlyargs()
        #for kw in self.__kwonlyargs:
        #    assert kw not in defined_args, "Multiple definitions of argument '{}' provided".format(arg)
        #    env.bind(kw, kw_args[kw])
        #    defined_args.add(kw)

        ## Kwarg
        #kwarg = args.kwarg()
        #if kwarg:
        #    env.bind(self.__kwarg, )

    def returns(self):
        """
        Find the return types of this function.
        """
        env = self.__env

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
        #env = inference.Environment.from_parent_env(parent_env)
        env = inference.Environment(parent_env=parent_env)

        # Add the arguments as variables
        env.parse_arguments(node.args)

        # Save arguments
        pos_args = []
        keywords = []
        vararg = None
        kwonlyargs = set()  # Order does not matter for this
        kwarg = None

        args_node = node.args

        # Positional
        pos_arg_nodes = args_node.args
        pos_end = len(pos_arg_nodes) - len(args_node.defaults)
        for arg in pos_arg_nodes[:pos_end]:
            pos_args.append(arg.arg)

        # Keywords
        for arg in pos_arg_nodes[pos_end:]:
            keywords.append(arg.arg)

        # Vararg
        if args_node.vararg:
            vararg = args_node.vararg.arg

        # Kwonlyargs
        for arg in args_node.kwonlyargs:
            kwonlyargs.add(arg.arg)

        # Kwarg
        if args_node.kwarg:
            kwarg = args_node.kwarg.arg

        return cls(node.name, env, node,
                   pos_args=pos_args,
                   keywords=keywords,
                   vararg=vararg,
                   kwonlyargs=kwonlyargs,
                   kwarg=kwarg)


"""
Create builtin variables
"""

class IntType(PyType):
    def __init__(self):
        super().__init__("int")

    def __hash__(self):
        return id(self.name())

    def __eq__(self, other):
        return isinstance(other, IntType)


def load_builtin_vars():
    types = [
        IntType(),
    ]
    return {t.name(): {t} for t in types}

