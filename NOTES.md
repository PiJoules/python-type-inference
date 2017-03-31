Python Program
--------------
Parse each node in the python program. These are the only actions you should perform when the 
appropriate node is hit:
- Bind variables to environments
- Create new pytypes
- Bind attributes to pytypes 
- Call functions

Any nodes that influence control flow have all outcome bodies parsed and any conditions evaluated.
For example, in an if/elif/else ladder, the bodies of each ladder are run in succession and the 
conditions for each if/elif are evaluated in order.


inferene.py 
-----------
- Only update types when an appropriate action is done in the python program 
  - Run set_attr() or bind() when something is being set in python space
  - Run get_attr() or lookup() when something is being looked up or accessed in python space
