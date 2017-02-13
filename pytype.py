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


class RunnableType(PyType):
    """
    Type that can contain code to be executed.
    """
    def __init__(self, env, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__env = env  # inference.Environment

    def env(self):
        return self.__env


class ModuleType(RunnableType):
    @classmethod
    def from_code(cls, code):
        return cls(inference.ModuleEnv())


"""
Create builtin variables
"""

class IntType(PyType):
    def __init__(self):
        super().__init__("int")

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return isinstance(other, IntType)


def load_builtin_vars():
    types = [
        IntType(),
    ]
    return {t.name(): {t} for t in types}

