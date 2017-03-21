import class_type


class BoolClass(class_type.ClassType):
    def __init__(self):
        super().__init__("bool")


def create_class():
    # Create the class
    cls = BoolClass()

    # Add any methods
    pass

    return cls


BOOL_CLASS = create_class()
