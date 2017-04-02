import pytype


class ClassType(pytype.PyType):
    def __init__(self, defined_name=None, inst=None, *args, **kwargs):
        super().__init__("type", *args, **kwargs)
        self.__inst = inst
        self.__defined_name = inst.name() if inst else defined_name

    @classmethod
    def from_node_and_env(cls, node, parent_env):
        """
        This method is used for creating from a cusotm class defined in
        python code.

        Interperet the contents of the class and add any assignments as
        attributes of the class.
        """
        from inference import Environment

        # Create an env to find assigned variables
        env = Environment(parent_env=parent_env)

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

    def instance(self):
        """Getter for getting the instance this class produces without calling init."""
        if self.__inst is None:
            from instance_type import InstanceType
            self.__inst = InstanceType(self.defined_name(), parents=[self])
        return self.__inst

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

