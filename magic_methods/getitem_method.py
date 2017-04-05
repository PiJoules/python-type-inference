from function_type import BuiltinFunction


class GetItemMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.GETITEM_METHOD,
            pos_args=["self", "key"],
        )
