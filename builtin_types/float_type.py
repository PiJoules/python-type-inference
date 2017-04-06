from class_type import ClassType
from function_type import BuiltinFunction
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


class FloatClass(ClassType):
    def __init__(self):
        super().__init__(
            "float",
            init_methods=(
                FloatAddMethod(),
                FloatSubMethod(),
                FloatMulMethod(),
                FloatTrueDivMethod(),
            )
        )
