import pytype
import astor
import pkgutil
import sys

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


class ModuleType(pytype.PyType):
    def __init__(self, ref_node, *args, **kwargs):
        super().__init__("module", *args, **kwargs)
        self.__ref_node = ref_node


class MathModuleType(ModuleType):
    def __init__(self):
        super().__init__(None)

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        return isinstance(other, type(self)) and hash(self) == hash(other)


def load_builtin_modules():
    from float_type import FLOAT_CLASS

    math_mod = MathModuleType()
    math_mod.set_attr("pi", {FLOAT_CLASS.instance()})

    return {
        "math": math_mod,
    }


BUILTIN_MODULES = load_builtin_modules()
