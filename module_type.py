import pytype
import astor
import pkgutil


def builtin_module_file_path(name):
    """
    Returns:
        (None, str): None if the module cannot be imported. The string path
            otherwise.
    """
    loader = pkgutil.get_loader(name)
    if loader is None:
        return loader
    return loader.path


def load_module(name):
    try:
        mod_t = self.lookup_module(name)
    except KeyError:
        if self.__module_location:
            mod_t = module_type.ModuleType.from_path(self.__module_location)
        else:
            raise RuntimeError("Path to main module required for non-builtin module")
    raise NotImplementedError


def module_location(mod_name):
    raise NotImplementedError


class ModuleType(pytype.PyType):
    def __init__(self, ref_node, *args, **kwargs):
        super().__init__("module", *args, **kwargs)
        self.__ref_node = ref_node

    @classmethod
    def from_path(cls, path):
        """
        Convert the file to an ast
        """
        raise NotImplementedError
