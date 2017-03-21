import class_type


class NoneClass(class_type.ClassType):
    def __init__(self):
        super().__init__("None")


def create_class():
    # Create the class
    cls = NoneClass()

    # Add any methods
    pass

    return cls


NONE_CLASS = create_class()
