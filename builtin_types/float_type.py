from class_type import StaticClassType
from magic_methods import *


class FloatAddMethod(AddMethod):
    def returns(self):
        return self.env().lookup("self")


class FloatSubMethod(SubMethod):
    def returns(self):
        return self.env().lookup("self")


class FloatMulMethod(MulMethod):
    def returns(self):
        return self.env().lookup("self")


class FloatTrueDivMethod(TrueDivMethod):
    def returns(self):
        return self.env().lookup("self")


class FloatClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__(
            "float",
            builtins,
            init_methods=(
                FloatAddMethod(builtins),
                FloatSubMethod(builtins),
                FloatMulMethod(builtins),
                FloatTrueDivMethod(builtins),
            )
        )
