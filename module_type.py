import pytype
import astor
import pkgutil


def module_path_from_name(name):
    """
    Returns:
        (None, str): None if the module cannot be imported. The string path
            otherwise (absolute).
    """
    loader = pkgutil.get_loader(name)
    if loader is None:
        return loader
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
    mod_location = module_path_from_name(name)
    if mod_location is None:
        raise RuntimeError("The module '{}' cannot be found on the pythonpath: {}.".format(name, sys.path))
    mod_node = module_node_from_path(mod_location)
    if mod_node is None:
        # The module is probably implemented in C
        # See if we have a ModuleType for it
        if name not in BUILTIN_MODULES:
            raise RuntimeError("The module '{}' is probably implemented in C and does not have a python implementation. This module should have a pre-built ModuleType.".format(name))
        else:
            return BUILTIN_MODULES[name]
    return ModuleType.from_node(mod_node)


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
    from pytype import FLOAT_TYPE

    math_mod = MathModuleType()
    math_mod.add_attr("pi", {FLOAT_TYPE})

    return {
        "math": math_mod,
    }


BUILTIN_MODULES = load_builtin_modules()
