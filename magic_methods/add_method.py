from function_type import FunctionType


class AddMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.ADD_METHOD, builtins,
            pos_args=["self", "other"]
        )
