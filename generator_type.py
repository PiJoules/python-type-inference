from instance_type import InstanceType
from class_type import ClassType
from builtin_types import NONE_TYPE


GENERATOR_NAME = "generator"


class GeneratorType(InstanceType):
    def __init__(self, yields=None, returns=None, *args, **kwargs):
        super().__init__("generator", *args, **kwargs)

        self.__yields = yields or set()
        self.__returns = returns or {NONE_TYPE}

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


class GeneratorClass(ClassType):
    def __init__(self, *args, **kwargs):
        super().__init__(
            defined_name=GENERATOR_NAME,
            *args, **kwargs
        )

    def instance(self, *args, **kwargs):
        return GeneratorType(parents=[self], *args, **kwargs)


def create_class():
    from function_type import BuiltinFunction

    cls = GeneratorClass()

    class GeneratorIterMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name=self.ITER_METHOD,
                pos_args=["self"]
            )

        def adjusted_call(self, args):
            self.check_pos_args(args)
            return args.pos_args()[0]

    class GeneratorNextMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name=self.NEXT_METHOD,
                pos_args=["self"]
            )

        def adjusted_call(self, args):
            self.check_pos_args(args)

            self_types = args.pos_args()[0]
            results = set()

            for self_t in self_types:
                results |= self_t.yields()

            return results

    cls.set_attr(cls.ITER_METHOD, {GeneratorIterMethod()})
    cls.set_attr(cls.NEXT_METHOD, {GeneratorNextMethod()})

    return cls


GENERATOR_CLASS = create_class()
