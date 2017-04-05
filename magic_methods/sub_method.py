from function_type import BuiltinFunction


class SubMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            self.SUB_METHOD,
            pos_args=["self", "other"]
        )
