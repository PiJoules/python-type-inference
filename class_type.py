from pytype import PyType
from function_type import FunctionType
from environment import Environment
from instance_type import InstanceType


class ClassType(PyType):
    def __init__(self, defined_name, builtins, init_methods=None, **kwargs):
        super().__init__("type", builtins, **kwargs)
        self.__defined_name = defined_name
        self.__inst = None
        methods = init_methods or []
        for method in methods:
            self.set_builtin_method(method)

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

    def defined_name(self):
        """The name for the type of instances this class produces."""
        return self.__defined_name

    def call(self, args):
        self.instance().call_init(args)
        return {self.instance()}

    def instance(self, *args, **kwargs):
        """Getter for getting the instance this class produces without calling init."""
        if self.__inst is None:
            self.__inst = InstanceType(self.defined_name(), self.builtins(), parents=[self], **kwargs)
        return self.__inst

    def set_builtin_method(self, method):
        assert isinstance(method, FunctionType)
        assert method.defined_name()
        self.set_attr(method.defined_name(), {method})

    def __hash__(self):
        # All classes are unique
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


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

    def instance(self, *args, **kwargs):
        return self.__inst_cls(*args, **kwargs)
