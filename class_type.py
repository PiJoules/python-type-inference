from pytype import PyType
from function_type import FunctionType
from environment import Environment
from instance_type import InstanceType

"""
Types of classes:
- Class that returns the same instance. Values associated with this type at
  runtime do not influence the type of the object. Classes like this include
  some builtin types like str() or int(), or custom user defined types in
  program space since these classes use the builtins.
- Class that creates instances which depend on types at runtime. Examples of
  this type of class include
"""


class ClassType(PyType):
    def __init__(self, builtins, init_methods=None, **kwargs):
        super().__init__("type", builtins, **kwargs)
        methods = init_methods or []
        for method in methods:
            self.set_builtin_method(method)

    def defined_name(self):
        """The name for the type of instances this class produces."""
        raise NotImplementedError

    def call(self, args):
        self.instance().call_init(args)
        return {self.instance()}

    def instance(self, *args, **kwargs):
        """Getter for getting the instance this class produces without calling init."""
        raise NotImplementedError

    def set_builtin_method(self, method):
        """Wrapper for set_attr() to just set 1 method."""
        assert isinstance(method, FunctionType)
        assert method.defined_name()
        self.set_attr(method.defined_name(), {method})

    def __hash__(self):
        # All classes are unique
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


class StaticClassType(ClassType):
    def __init__(self, defined_name, builtins, inst=None, **kwargs):
        super().__init__(builtins, **kwargs)
        self.__inst = inst or InstanceType(defined_name, self.builtins(), parents=[self])

    def defined_name(self):
        return self.instance().name()

    def instance(self, *args, **kwargs):
        return self.__inst

    @classmethod
    def from_node_and_env(cls, node, parent_env):
        """
        This method is used for creating from a cusotm class defined in
        python code.

        Interperet the contents of the class and add any assignments as
        attributes of the class.
        """
        # Create an env to find assigned variables
        env = Environment(node.name, parent_env=parent_env)

        # Parse the class body
        env.parse_sequence(node.body)

        # Convert all saved variables to attributes
        return cls.from_name(node.name, env.builtins(), init_attrs=env.variables())


class DynamicClassType(ClassType):
    """
    Class types of this kind will return instances whose type is dependant on
    what happens at runtime. An example of this can be a list which acts as
    a container. The contents of a list depend on what is inserted into it at
    runtime, and a list that contains integers is a different type from a list
    that contains integers and floats.

    For this type of class, the instance() method will return new instances
    of the instance type instead of the same one repeatedly.
    """
    def __init__(self, builtins, inst_cls, **kwargs):
        super().__init__(builtins, **kwargs)
        self.__inst_cls = inst_cls

    def defined_name(self):
        return self.__inst_cls.__name__

    def instance(self, *args, **kwargs):
        return self.__inst_cls(*args, parents=[self], **kwargs)
