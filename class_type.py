import pytype

from function_type import FunctionType


class ClassType(pytype.PyType):
    def __init__(self, builtins, defined_name=None, init_methods=None, inst=None, *args, **kwargs):
        super().__init__("type", builtins, *args, **kwargs)
        self.__inst = inst
        self.__defined_name = inst.name() if inst else defined_name
        assert self.__defined_name

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
        from environment import Environment

        # Create an env to find assigned variables
        env = Environment(node.name, parent_env=parent_env)

        # Parse the class body
        env.parse_sequence(node.body)

        # Convert all saved variables to attributes
        return cls(node.name, init_attrs=env.variables())

    def defined_name(self):
        """The name for the type of instances this class produces."""
        return self.__defined_name

    def call(self, args):
        self.instance().call_init(args)
        return {self.instance()}

    def instance(self, *args, **kwargs):
        """Getter for getting the instance this class produces without calling init."""
        if self.__inst is None:
            from instance_type import InstanceType
            self.__inst = InstanceType(self.defined_name(), parents=[self], *args, **kwargs)
        return self.__inst

    def set_builtin_method(self, method):
        from function_type import FunctionType
        assert isinstance(method, FunctionType)
        assert method.defined_name()
        self.set_attr(method.defined_name(), {method})

    def __hash__(self):
        # All classes are unique
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


class InstanceWrapperClass(ClassType):
    def call(self, args):
        raise NotImplementedError("Instance wrapper must return the custom instance each time")

    def instance(self, *args, **kwargs):
        raise NotImplementedError("Instance wrapper must return the custom instance each time")

