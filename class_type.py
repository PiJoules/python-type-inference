import ast

import inference
import pytype
import instance_type


class ClassType(pytype.PyType):
    def __init__(self, defined_name, *args, **kwargs):
        super().__init__("type", *args, **kwargs)
        self.__inst = None
        self.__defined_name = defined_name

    @classmethod
    def from_node_and_env(cls, node, parent_env):
        """
        This method is used for creating from a cusotm class defined in
        python code.

        Interperet the contents of the class and add any assignments as
        attributes of the class.
        """
        # Create an env to find assigned variables
        env = inference.Environment(parent_env=parent_env)

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
            self.__inst = instance_type.InstanceType(self)
        return self.__inst

    def __hash__(self):
        # All classes are unique
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


class BuiltinClass(ClassType):
    def __init__(self):
        super().__init__(None)

    def call(self, args):
        raise NotImplementedError
