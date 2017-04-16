import ast
import sys
import astunparse


def is_ge_v3_5():
    info = sys.version_info
    return info[0] >= 3 and info[1] >= 5


def create_type_tracker():
    return ast.Assign(
        targets=[ast.Name("TYPES", None)],
        value=ast.Dict([], [])
    )


class NoValue:
    pass


class ValueType:
    def __init__(self, name, init_attrs=None, value=NoValue):
        self.__name = name
        self.__value = value
        self.__attrs = init_attrs or {}

    def attrs(self):
        return self.__attrs

    def get_attr(self, attr):
        return self.__attrs[attr]


class FunctionType:
    def __init__(self, name, pos=None, kw=None, var=None, kwonly=None,
                 kwarg=None,
                 kwdef=None,
                 return_t=None):
        self.__name = name
        self.__pos = pos or []
        self.__kw = kw or []
        self.__var = var
        self.__kwonly = kwonly or {}
        self.__kwarg = kwarg
        self.__return_t = return_t or set()

    def pos(self):
        return self.__pos

    def kw(self):
        return self.__kw

    def var(self):
        return self.__var

    def kwonly(self):
        return self.__kwonly

    def kwarg(self):
        return self.__kwarg

    def return_t(self):
        return self.__return_t


class UserDefinedFunction(FunctionType):
    def __init__(self, node):
        name = node.name
        args = node.args  # Arguments node
        body = node.body

        super().__init__(name)

        self.__body = body

    def body(self):
        return self.__body



class TreeEditor(ast.NodeTransformer):
    def __init__(self, name="__main__"):
        super().__init__()
        self.__name = name
        self.__vars = {}

    def visit_seq(self, seq):
        for node in seq:
            self.visit(node)

    def visit_Module(self, node):
        for child in node.body:
            self.visit(child)
        return ast.Module(
            body=[create_type_tracker()] + node.body
        )

    def visit_FunctionDef(self, node):
        func = UserDefinedFunction(node)
        self.__vars[node.name] = func

    def visit_If(self, node):
        test = node.test
        body = node.body
        orelse = node.orelse

        self.visit(test)
        self.visit_seq(body)
        self.visit_seq(orelse)

    def visit_Call(self, node):
        func = node.func  # ast node

        if not is_ge_v3_5():
            raise NotImplementedError("Need to implement logic for call in v3.4 or earlier")

        raise NotImplementedError


def main():
    fname = sys.argv[1]
    with open(fname, "r") as f:
        code = f.read()
    original_ast = ast.parse(code)

    new_ast = TreeEditor().visit(original_ast)

    print(astunparse.unparse(new_ast))

    return 0


if __name__ == "__main__":
    main()
