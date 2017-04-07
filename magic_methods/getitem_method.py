from function_type import FunctionType


class GetItemMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.GETITEM_METHOD, builtins,
            pos_args=["self", "key"],
        )
