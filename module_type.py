import astor
import pkgutil
import sys

from pytype import PyType
from importlib.machinery import SourceFileLoader


def module_path_from_name(name):
    """
    Returns:
        (None, str): None if the module cannot be imported. The string path
            otherwise (absolute).
    """
    loader = pkgutil.get_loader(name)
    if not isinstance(loader, SourceFileLoader):
        return None
    return loader.path


def module_node_from_path(path):
    try:
        node = astor.parsefile(path)
    except:
        return None
    else:
        return node


def load_module(name):
    """
    Returns:
        ModuleType

    Raises:
        RuntimeError
    """
    # Check the sys path first
    mod_location = module_path_from_name(name)
    if mod_location:
        mod_node = module_node_from_path(mod_location)
        if mod_node:
            return ModuleType.from_node(mod_node)

    # Then check the builtins that were implemented
    if name in BUILTIN_MODULES:
        return BUILTIN_MODULES[name]
    else:
        raise RuntimeError("The module '{}' is probably implemented in C and does not have a python implementation. This module should have a pre-built ModuleType.".format(name))


class ModuleType(PyType):
    def __init__(self, defined_name, builtins, **kwargs):
        super().__init__("module", builtins, **kwargs)
        self.__defined_name = defined_name

    def defined_name(self):
        return self.__defined_name


class MathModuleType(ModuleType):
    def __init__(self, builtins):
        super().__init__(
            "math",
            builtins,
            init_attrs={
                "pi": {builtins.float()},
            }
        )

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        return isinstance(other, type(self)) and hash(self) == hash(other)
