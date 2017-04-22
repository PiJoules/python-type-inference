class PyType:
    def __init__(self, value=None):
        self.__value = value

    def call(self, *args, **kwargs):
        return self.__value(*args, **kwargs)

    @classmethod
    def from_func(cls, func):
        return cls(value=func)


class StrType(PyType):
    pass


def load_global_consts():
    return {
        "__name__": PyType(),
    }


def load_global_vars():
    return {
        "bool": PyType(),
    }


class FrameTracker:
    def __init__(self, name, init_vars=None):
        self.__name = name
        self.__variables = init_vars or {}
        self.__returns = set()
        self.__call_stack = set()

    def name(self):
        return self.__name

    def _check_type(self, t):
        if t == DelayedType:
            raise RuntimeError

    def call_stack(self):
        return self.__call_stack

    def returns(self):
        if not self.__returns:
            raise RuntimeError("Return types for callable '{}'".format(self.name()))
        return self.__returns

    def variables(self):
        return self.__variables

    def bind_variable(self, varname, types):
        if varname in self.__variables:
            self.__variables[varname] |= types
        else:
            self.__variables[varname] = set(types)

    def bind_function(self, func):
        assert callable(func)
        self.bind_variable(func.__name__, {PyType.from_func(func)})

    def bind_returns(self, inst):
        self.__returns.add(type(inst))

    def call_func(self, func, *args, **kwargs):
        """
        Keep track of a called function.
        """
        if func not in self.__call_stack:
            self.__call_stack.add(func)
            result = func(*args, **kwargs)
            self.__call_stack.remove(func)
            return result
        else:
            return DelayedType

    def lookup(self, varname):
        return self.__variables[varname]


class GlobalFrameTracker(FrameTracker):
    def __init__(self, **kwargs):
        super().__init__(
            "__main__", init_vars=load_global_vars(), **kwargs)
