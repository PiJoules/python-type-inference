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

    def __init__(self, pos_args, vararg, keyword_args, kwarg):
        """
        Args:
            pos_args (list[set[pytype.PyType]])
            vararg (Optional[pytype.PyType])
            keyword_args (dict[str, set[pytype.PyType]])
            kwarg (Optional[pytype.PyType])
        """
        assert isinstance(pos_args, list)
        assert all(isinstance(x, set) for x in pos_args)

        assert isinstance(keyword_args, dict)
        assert all(isinstance(x, set) for x in pos_args)

        self.__pos_args = pos_args
        self.__vararg = vararg
        self.__keyword_args = keyword_args
        self.__kwarg = kwarg

    def pos_args(self):
        return self.__pos_args

    def vararg(self):
        return self.__vararg

    def keyword_args(self):
        return self.__keyword_args

    def kwarg(self):
        return self.__kwarg

    @classmethod
    def from_call_node_v3_4_older(cls, node, ref_env):
        raise NotImplementedError("Implement logic for evaluating calls in 3.4")

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

        return cls(pos_args, vararg, keyword_args, kwarg)

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

