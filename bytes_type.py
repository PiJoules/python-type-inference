import class_type


class BytesType(class_type.ClassType):
    def __init__(self):
        super().__init__("bytes")


def create_class():
    cls = BytesType()

    return cls


BYTES_CLASS = create_class()
