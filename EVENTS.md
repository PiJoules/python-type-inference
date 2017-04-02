4/2/2017
- Make sure your __hash__ implementations do not depend on mutable properties in an object because when they are placed in sets, and then you update that property, the hash that the set knows the object as does not change.
