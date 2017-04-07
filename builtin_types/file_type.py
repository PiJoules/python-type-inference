from class_type import StaticClassType


class FileClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__("file", builtins)
