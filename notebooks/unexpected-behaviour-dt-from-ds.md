# When creating a DataTree from a Dataset with path-like variable, subgroups are expected to be created


```python
from pathlib import Path

import numpy as np
import xarray as xr
import datatree as dt 
from xarray import open_zarr
```


```python
# Set to True to get rich HTML representations in an interactive Notebook session
# Set to False to get textual representations ready to be converted to markdown for issue report

INTERACTIVE = False 

# Convert to markdown with
# jupyter nbconvert --to markdown notebooks/unexpected-behaviour-dt-from-ds.ipynb
```

### Test Data Initialization

A Dataset containing a single variable, with a name containing slashes, representing a path.


```python
xda = xr.DataArray(
    np.arange(3 * 18).reshape(3, 18),
    coords={"label": list("abc"), "z": list(range(18))},
)
xda = xda.chunk({"label": 2, "z": 4})
xds = xr.Dataset({"group/subgroup/my_variable": xda})
xds if INTERACTIVE else print(xds)
```

    <xarray.Dataset>
    Dimensions:                     (label: 3, z: 18)
    Coordinates:
      * label                       (label) <U1 'a' 'b' 'c'
      * z                           (z) int64 0 1 2 3 4 5 6 ... 11 12 13 14 15 16 17
    Data variables:
        group/subgroup/my_variable  (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


This flat Dataset containing path-like variable name is expected to produce groups and subgroups
once injected into a DataTree.

Unfortunately, it does not happen. Instead it produces a flat DataTree with a single variable,
with an illegal name (containing slashes).


```python
xdt = dt.DataTree(xds)
xdt if INTERACTIVE else print(xdt)
```

    DataTree('None', parent=None)
        Dimensions:                     (label: 3, z: 18)
        Coordinates:
          * label                       (label) <U1 'a' 'b' 'c'
          * z                           (z) int64 0 1 2 3 4 5 6 ... 11 12 13 14 15 16 17
        Data variables:
            group/subgroup/my_variable  (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


This is not only cosmetic. Indeed, trying to access this malformed variable name will result in an error:


```python
try: 
    xdt["group/subgroup/my_variable"]
except KeyError as err:
    print(err)
```

    'Could not find node at group/subgroup/my_variable'


The expected behaviour would be the one of using `__setitem__`:


```python
xdt = dt.DataTree()
for varname, xda in xds.items():
    xdt[varname] = xda
xdt if INTERACTIVE else print(xdt)
```

    DataTree('None', parent=None)
    └── DataTree('group')
        └── DataTree('subgroup')
                Dimensions:      (label: 3, z: 18)
                Coordinates:
                  * label        (label) <U1 'a' 'b' 'c'
                  * z            (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
                Data variables:
                    my_variable  (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


### Technical Hints

`__setitem__` wraps the key into a `NodePath`:

https://github.com/xarray-contrib/datatree/blob/0afaa6cc1d6800987d8b9c37a604dc0a8c68aeaa/datatree/datatree.py#L923

Probably this section of the DataTree initialization logic would need to be adapted:

https://github.com/xarray-contrib/datatree/blob/0afaa6cc1d6800987d8b9c37a604dc0a8c68aeaa/datatree/datatree.py#L408


## Discussion

https://github.com/xarray-contrib/datatree/issues/311#issuecomment-1944364934

Hello, thanks for your answer!

Indeed the round-trip capability seems the cleanest default behaviour. A Dataset is supposed to be a group. I think what I needed already exists: it's `DataTree.from_dict` .

https://github.com/xarray-contrib/datatree/blob/0afaa6cc1d6800987d8b9c37a604dc0a8c68aeaa/datatree/datatree.py#L1035

I can have a look to fix the bug (forbidding Datasets containing path-like variable names), and I can suggest an error message like this to help the user that probably wanted this "auto-creating-group" behaviour but did not knew about `.from_dict`:

```
Given Dataset contains path-like variable names. 
A Dataset represents a group, and a single group cannot have path-like variable names.
Consider `DataTree.from_dict` to automatically create groups from a mapping of paths to data objects
```

(if you have an idea to shorten and improve it I am interested!)

Here is what I really wanted to do when creating the issue:


```python
from pathlib import PurePosixPath

# Note: paths represent variable names ; the mapping should only contain groups, hence `.parent`
# Note 2: the named DataArray is renamed to only keep the name part of the path.
mapping_path_to_dataarray = {
    PurePosixPath(str(varname)).parent: xda.rename(PurePosixPath(str(varname)).name)
    for varname, xda in xds.items()
}
mapping_path_to_dataarray
```




    {PurePosixPath('group/subgroup'): <xarray.DataArray 'my_variable' (label: 3, z: 18)>
     dask.array<xarray-<this-array>, shape=(3, 18), dtype=int64, chunksize=(2, 4), chunktype=numpy.ndarray>
     Coordinates:
       * label    (label) <U1 'a' 'b' 'c'
       * z        (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17}



Though this logic will work, it seems a little bit over-complicated to me.
However, a Dataset carrying variables names containing paths is a little bit 
a misuse of a Dataset. A DataTree should be used in the first place
if possible.


```python
xdt = dt.DataTree.from_dict(mapping_path_to_dataarray)
xdt if INTERACTIVE else print(xdt)
```

    DataTree('None', parent=None)
    └── DataTree('group')
        └── DataTree('subgroup')
                Dimensions:      (label: 3, z: 18)
                Coordinates:
                  * label        (label) <U1 'a' 'b' 'c'
                  * z            (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
                Data variables:
                    my_variable  (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


Note: Pylance is not happy of usage of dict of PurePosixPaths. It only expects str as keys.
Maybe it could be worth it to make it accepts Pure Paths too?

```
Argument of type "dict[PurePosixPath, DataArray]" cannot be assigned to parameter "d" of type "MutableMapping[str, Dataset | DataArray | DataTree[Unknown] | None]" in function "from_dict"
  "dict[PurePosixPath, DataArray]" is incompatible with "MutableMapping[str, Dataset | DataArray | DataTree[Unknown] | None]"
    Type parameter "_KT@MutableMapping" is invariant, but "PurePosixPath" is not the same as "str"
    Type parameter "_VT@MutableMapping" is invariant, but "DataArray" is not the same as "Dataset | DataArray | DataTree[Unknown] | None"PylancereportArgumentType
```

Reconverting the DataTree gives an empty Dataset, as the root contains only groups 
but no concrete variables:


```python
reconverted = xdt.to_dataset()
reconverted if INTERACTIVE else print(reconverted)
```

    <xarray.Dataset>
    Dimensions:  ()
    Data variables:
        *empty*


Reconverting the subgroup containing the variable is successful


```python
reconverted = xdt["group/subgroup"].to_dataset()
reconverted if INTERACTIVE else print(reconverted)
```

    <xarray.Dataset>
    Dimensions:      (label: 3, z: 18)
    Coordinates:
      * label        (label) <U1 'a' 'b' 'c'
      * z            (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
    Data variables:
        my_variable  (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>

