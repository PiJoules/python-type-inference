from class_type import ClassType


class SliceClass(ClassType):
    def __init__(self):
        super().__init__("slice")


def create_class():
    cls = SliceClass()

    return cls


SLICE_CLASS = create_class()
