from function_type import BuiltinFunction


class ContainsMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.CONTAINS_METHOD,
            pos_args=["self", "item"],
        )
