import ast

import inference
import pytype


class ClassType(pytype.PyType):
    @classmethod
    def from_node_and_env(cls, node, parent_env):
        raise NotImplementedError

    def create_instance(self, args):
        self.call_init(args)
        return self.returns()
