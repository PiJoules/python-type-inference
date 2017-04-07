from class_type import StaticClassType


class SliceClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__("slice", builtins)
