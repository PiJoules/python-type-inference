from function_type import FunctionType


class IAddMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.IADD_METHOD, builtins,
            pos_args=["self", "other"],
        )
