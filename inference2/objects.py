# -*- coding: utf-8 -*-

import object_types


class Object(object):
    """
    A class representing something that exists in the env and accessible at
    runtime.
    """
    def types(self):
        """
        The actual type of the variable.

        Represents what is returned from "type(obj)", but this variable could
        be contain mutliple types.

        Literals always have types that are sets of size 1.

        Returns:
            set[Type]
        """
        raise NotImplementedError

    def return_types(self, call_stack=None):
        """
        The types returned when this variable is called.

        Varies by type. Functions will have this, but literals may not.
        Classes will use this.

        Args:
            call_stack (Optional[set[str]]): Set containing previously called
                functions/objects.

        Returns:
            set[Type]
        """
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(self, type(other)) and (hash(self) == hash(other))

    def __ne__(self, other):
        return not (self == other)


"""
Builtin objects
"""

class FunctionObject(Object):
    def __init__(self, node, env, owner=None):
        pass

    def types(self):
        pass


class LiteralObject(Object):
    def __init__(self, literal_type):
        assert isinstance(literal_type, object_types.Type)
        self.__type = literal_type

    def types(self):
        return {self.__type}

    def __hash__(self):
        return hash(frozenset({t.name() for t in self.types()}))


class IntObject(LiteralObject):
    pass

class FloatObject(LiteralObject):
    pass


class ListObject(LiteralObject):
    """
    List object for manually keeping track of contents at runtime since
    this type is hardcoded into the python interpetter.

    Do not remove any contents to keep track of the types.
    """
    def __init__(self, list_type, default, contents):
        """
        Args:
            default (Type): The default content type if this object does not
                contain anything.
            init_contents (Optional[list[Object]]): Initial contents of the
                list.
        """
        super().__init__(list_type)
        self.__contents = contents
        self.__default = default

        assert isinstance(self.__contents, list)
        assert all(isinstance(x, Object) for x in self.__contents)

    def contents(self):
        """
        Returns:
            list[Object]
        """
        return self.__contents

    def content_types(self):
        """
        Set containing all types of variables that this type can contain.

        Returns:
            set[Type]
        """
        if self.__contents:
            types = set()
            for obj in self.__contents:
                types |= obj.types()
            return types
        else:
            return {self.__default}

    """
    Wrapper methods for all list methods.
    """


