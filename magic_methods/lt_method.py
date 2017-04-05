from function_type import BuiltinFunction


class LtMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.LT_METHOD,
            pos_args=["self", "other"],
        )
