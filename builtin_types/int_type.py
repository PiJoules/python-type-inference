from class_type import ClassType
from magic_methods import *

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
        from builtin_types import FLOAT_TYPE
        others = self.env().lookup("other")
        results = set()
        for other_t in others:
            if other_t.is_type(INT_TYPE):
                results.add(FLOAT_TYPE)
            elif other_t.is_type(FLOAT_TYPE):
                results.add(FLOAT_TYPE)
            else:
                raise RuntimeError("Unable to divide int by {}".format(other_t))
        return results


class IntLtMethod(LtMethod):
    def returns(self):
        from builtin_types import BOOL_TYPE
        return {BOOL_TYPE}


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
