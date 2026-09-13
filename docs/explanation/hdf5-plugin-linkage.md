# The linkage of the hdf5 filters

A filter is loaded into a process that already runs hdf5,
so the linkage of that hdf5 reaches into the filters themselves.
Against a shared hdf5 they link it as well.
Against a static one they are built with the hdf5 symbols left undefined,
and resolve them against the program that loads them.
The lookup works only if the program exports its own symbols.
The recipe asks for that through a link flag,
so a consumer needs no change of its own.
