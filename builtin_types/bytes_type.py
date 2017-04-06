from class_type import ClassType


class BytesType(ClassType):
    def __init__(self):
        super().__init__("bytes")


BYTES_CLASS = BytesType()
BYTES_TYPE = BYTES_CLASS.instance()
