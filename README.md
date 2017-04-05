# Python Type Inference
Get the types of variables in python code.

## How it works
The package works by keeping track of variable assignments and types passed to arguments. 
For example, given the statement `x = 2`, I know that the variable `x` is of type `int`.
If it was followed with `x = 3.0`, then x can be either an `int` or `float`. To this package,
the types associated with `x` is the set of an integer type and float type.

For function arguments, the types depend on the types of the variables passed to them.


## Usage
Examples of usage are in the test files. The following is code for finding the nth fibonacci number (in `samples/fib.py`):

```py 
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)


def main():
    print(fib(5))
    return 0


if __name__ == "__main__":
    main()
```

The following is a test for for checking various types in the above python code (located in `test_samples.py`):
```py 
class TestSamples(unittest.TestCase):
    def create_module_env(self, filepath):
        with open(filepath, "r") as f:
            env = ModuleEnv(module_location=filepath)
            env.parse_code(f.read())
            return env

    def first(self, container):
        self.assertEqual(len(container), 1)
        return next(iter(container))

    def test_fib(self):
        """Testing fib.py"""
        env = self.create_module_env("samples/fib.py")

        # main()
        main = self.first(env.exclusive_lookup("main"))
        self.assertSetEqual(
            main.returns(),
            {INT_CLASS.instance()}
        )

        # fib()
        fib = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            fib.env().exclusive_lookup("n"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            fib.returns(),
            {INT_CLASS.instance()}
        )
```


## Tests 
Run `nosetests` to run all modules that start with `test_`.
