from class_type import StaticClassType


class BoolClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__(
            "bool", builtins,
        )
