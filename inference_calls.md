# The following is what occurs by the inferencer
main_module = create_main_module()  # creates the __main__ module and internally creates a new module type

# definition of class A
class_inst = create_class_from_node(cls_def_node)  # pytype of class A
env.bind("A", {class_inst})  # binding in program space
main_module.set_attr("A", {class_inst})

# Instance creation of A 
inst = class_inst.call(args)  # args is an empty Arguments type 
env.bind("x", {inst})
main_module.set_attr("x", {inst})

# Set attribute of instance x 
x_types = env.lookup("x")
for t in x_types:
    int_literal_types = create_int()  # set[IntType]
    t.set_attr("b", int_literal_types)


-------------

class PyType:
    def __init__(self, name, init_attrs=None):
        self.__name = name
        self.__attrs = init_attrs or {}

    def set_attr(self, attr, types):
        ...

    def get_attr(self, attr):
        return self.__attrs[attr]

    def has_attr(self, attr):
        return attr in self.__attrs

    def name(self):
        return self.__name


class ModuleType(PyType):
    pass
