import ast

import inference
import pytype
import instance_type


class ClassType(pytype.PyType):
    def __init__(self, ref_node, *args, **kwargs):
        super().__init__("type", *args, **kwargs)
        self.__ref_node = ref_node

    @classmethod
    def from_node_and_env(cls, node, parent_env):
        """
        Interperet the contents of the class and add any assignments as
        attributes of the class.
        """
        # Create an env to find assigned variables
        env = inference.Environment(parent_env=parent_env)

        # Parse the class body
        env.parse_sequence(node.body)

        # Convert all saved variables to attributes
        return cls(node, init_attrs=env.variables())

    def defined_name(self):
        if self.__ref_node is None:
            return None
        return self.__ref_node.name

    def create_instance(self):
        return instance_type.InstanceType.from_class_type(self)

    def call_init(self, args):
        """
        Call the __init__ method of this class
        """
        raise NotImplementedError

    def create_and_init(self, args):
        inst_type = self.create_instance()
        inst_type.call_init(args)
        return {inst_type}

    def ref_node(self):
        return self.__ref_node

    def __hash__(self):
        # All classes are unique
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


class BuiltinClass(ClassType):
    def __init__(self):
        super().__init__(None)

    def create_and_init(self, args):
        raise NotImplementedError
