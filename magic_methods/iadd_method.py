from function_type import BuiltinFunction


class IAddMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.IADD_METHOD,
            pos_args=["self", "other"],
        )
