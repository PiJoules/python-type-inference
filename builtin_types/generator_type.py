from instance_type import InstanceType
from class_type import DynamicClassType
from magic_methods import *


GENERATOR_NAME = "generator"


class GeneratorType(InstanceType):
    def __init__(self, builtins, yields=None, returns=None, **kwargs):
        super().__init__(GENERATOR_NAME, builtins, **kwargs)

        self.__yields = yields or set()
        self.__returns = returns or {self.builtins().none()}

    def yields(self):
        return self.__yields

    def returns(self):
        return self.__returns

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        if not isinstance(other, GeneratorType):
            return False

        return (self.yields() == other.yields() and
                self.returns() == other.returns())

    def __str__(self):
        return "{}[yields={}, returns={}]".format(
            self.name(),
            list(map(str, self.yields())),
            list(map(str, self.returns()))
        )


class GeneratorIterMethod(IterMethod):
    def returns(self):
        return self.env().lookup("self")


class GeneratorNextMethod(NextMethod):
    def returns(self):
        self_types = self.env().lookup("self")
        results = set()

        for self_t in self_types:
            results |= self_t.yields()

        return results


class GeneratorClass(DynamicClassType):
    def __init__(self, builtins, **kwargs):
        super().__init__(
            builtins, GeneratorType,
            init_methods=(
                GeneratorIterMethod(builtins),
                GeneratorNextMethod(builtins),
            ),
            **kwargs
        )
