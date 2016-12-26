# -*- coding: utf-8 -*-


# Since NoneType is not actually defined, yet is returned by 'type(None)'
NoneType = type(None)


def optional(t):
    if isinstance(t, tuple):
        return t + (NoneType, )
    return (t, NoneType)


class Mixin(object):
    """
    Base mixin class used for describing objects that share mutliple parents.
    """

    def __init__(self, *args, **kwargs):
        # Make sure that the next parent is called
        super().__init__(*args, **kwargs)


class SlotDefinedClass(object):
    __slots__ = tuple()  # Names of attributes
    __types__ = {}  # Optional mapping of attribute to expected type
    __defaults__ = {}  # Optional default values for an attribute

    def __init__(self, *args, **kwargs):
        """
        - Note this must be placed last in the chain of parents since this
        method does not call super()
        """
        slots = self.__slots__
        defaults = self.__defaults__

        set_attrs = set()

        # Go through args first, then kwargs
        if len(args) > len(slots):
            raise RuntimeError("Too many arguments provided. Args {} provided for {} when args {} were expected.".format(args, type(self), slots))

        for i, val in enumerate(args):
            attr = slots[i]
            self.__check_and_set_attr(attr, val)
            set_attrs.add(attr)

        for attr in slots:
            if attr in set_attrs:
                # We already set this value in the args
                continue

            if attr in kwargs:
                val = kwargs[attr]
            elif attr in defaults:
                val = defaults[attr]
            else:
                raise RuntimeError("No value for attribute '{}' provided in class '{}'".format(attr, type(self)))

            self.__check_and_set_attr(attr, val)


    def __check_and_set_attr(self, attr, val):
        if attr in self.__types__:
            self.__check_type(attr, val, self.__types__[attr])
        setattr(self, attr, val)


    def __check_type(self, attr, val, expected):
        """Check that the appropriate type is used.

        If the attribute is meant to be a container, check the contents of the
        container. In this case, just the first element of the container is
        checked.

        Args:
            attr (str)
        """
        if isinstance(expected, (type, tuple)):
            # Base class
            assert isinstance(val, expected), \
                "Expected type '{}' for attribute '{}' in class '{}'. Got '{}'".format(
                    expected, attr, type(self), type(val)
                )
        elif isinstance(expected, list):
            # Check container
            self.__check_type(attr, val, list)

            # Check elements
            if val:
                self.__check_type(attr, val[0], expected[0])
        elif isinstance(expected, dict):
            # Check container
            self.__check_type(attr, val, dict)

            # Check keys and vals
            if val:
                self.__check_type(attr, next(iter(val.keys())), next(iter(expected.keys())))
                self.__check_type(attr, next(iter(val.values())), next(iter(expected.values())))
        else:
            raise RuntimeError("Uknown type handling for type '{}'".format(expected))


def merge_dicts(d1, d2):
    d1_copy = d1.copy()
    d1_copy.update(d2)
    return d1_copy


