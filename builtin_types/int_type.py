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
        others = self.env().lookup("other")
        results = set()
        for other_t in others:
            if other_t.is_type(self.builtins().int()):
                results.add(self.builtins().float())
            elif other_t.is_type(self.builtins().float()):
                results.add(self.builtins().float())
            else:
                raise RuntimeError("Unable to divide int by {}".format(other_t))
        return results


class IntLtMethod(LtMethod):
    def returns(self):
        return {self.builtins().bool()}


class IntClass(ClassType):
    def __init__(self, builtins):
        super().__init__(
            builtins,
            "int",
            init_methods=(
                IntAddMethod(),
                IntSubMethod(),
                IntMulMethod(),
                IntTrueDivMethod(),
                IntLtMethod(),
            )
        )
