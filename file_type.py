import class_type


class FileClass(class_type.ClassType):
    def __init__(self):
        super().__init__("file")


def create_class():
    cls = FileClass()

    return cls


FILE_CLASS = create_class()
