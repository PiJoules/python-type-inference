import class_type


class StrClass(class_type.ClassType):
    def __init__(self):
        super().__init__("str")


def create_class():
    # Create the class
    cls = StrClass()

    # Add any methods
    pass

    return cls


STR_CLASS = create_class()
