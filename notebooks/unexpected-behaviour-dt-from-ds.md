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

