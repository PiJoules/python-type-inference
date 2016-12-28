# Python Type Inference

## Installation
Inside a virtualenv, run
```sh
(venv) ./_setup.sh
```
This automatically installs the `inference` package into the venv for use.


## TODO
- Determine argument types from what is passed
- Method/attribute calls and method argument handling
- Unpacking for nested tuples/lists
  - Requires implementing of a struct type that contains ordered types
- Add logic for updating types in higher scopes that were declared as global or nonlocal in lower scopes
- Split up the test code into different unittests
- Logic for yields and raises
