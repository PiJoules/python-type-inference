from class_type import ClassType


class SliceClass(ClassType):
    def __init__(self):
        super().__init__("slice")


SLICE_CLASS = SliceClass()
SLICE_TYPE = SLICE_CLASS.instance()
