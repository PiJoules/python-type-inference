from class_type import ClassType
from magic_methods import *
from str_type import STR_CLASS
from float_type import FLOAT_CLASS
from bool_type import BOOL_CLASS

class IntAddMethod(AddMethod):
    def returns(self):
        return self.env().lookup("self")


class IntSubMethod(SubMethod):
    def returns(self):
        return self.env().lookup("self")


class IntMulMethod(MulMethod):
    def returns(self):
        # Return the type of other b/c the result will change
        # depending on what you multiply against this int
        return self.env().lookup("other")


class IntTrueDivMethod(TrueDivMethod):
    def returns(self):
        others = self.env().lookup("other")
        results = set()
        for other_t in others:
            if other_t.is_type(INT_TYPE):
                results.add(FLOAT_CLASS.instance())
            elif other_t.is_type(FLOAT_CLASS.instance()):
                results.add(FLOAT_CLASS.instance())
            else:
                raise RuntimeError("Unable to divide int by {}".format(other_t))
        return results


class IntLtMethod(LtMethod):
    def returns(self):
        return {BOOL_CLASS.instance()}


class IntClass(ClassType):
    def __init__(self):
        super().__init__(
            "int",
            init_methods=(
                IntAddMethod(),
                IntSubMethod(),
                IntMulMethod(),
                IntTrueDivMethod(),
                IntLtMethod(),
            )
        )


INT_CLASS = IntClass()
INT_TYPE = INT_CLASS.instance()
