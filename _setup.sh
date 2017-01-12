python setup.py bdist_wheel
wheel install dist/parser_gen-?.?.?-py?-none-any.whl --force
wheel install-scripts inference
python setup.py develop

