import pytype


class ModuleType(pytype.PyType):
    def __init__(self, ref_node, *args, **kwargs):
        super().__init__("module", *args, **kwargs)
        self.__ref_node = ref_node

    @classmethod
    def from_path(cls, path):
        raise NotImplementedError
