# %%
from pathlib import Path

import numpy as np
import xarray as xr
from datatree import DataTree, open_datatree
from xarray import open_zarr

# %% [markdown]
# ## Data Creation
#

# %%
xda = xr.DataArray(
    np.arange(3 * 18).reshape(3, 18),
    coords={"label": list("abc"), "z": list(range(18))},
)
xda = xda.chunk({"label": 2, "z": 4})
xda

# %%
xdt = DataTree(xr.Dataset({"my_xda": xda}))
xdt.my_xda

# %% [markdown]
# ## Data Writing
#

# %%
zarr_path = Path() / "../generated/my_array.zarr"
xdt.to_zarr(zarr_path)

# %% [markdown]
# ## Data Reading
#

# %% [markdown]
# ### Using xarray's `open_zarr`
#
# See https://docs.xarray.dev/en/stable/generated/xarray.open_zarr.html
#
# Documentation version: `stable` at time of writing: 11 nov 2023
#
# Resulting behaviours serve as reference.

# %% [markdown]
# #### No `chunks` kwarg
#
# Stored chunks are used.

# %%
open_zarr(zarr_path).my_xda

# %% [markdown]
# #### With `chunks='auto'`
#
# Stored chunks are used.
#
# Same behaviour as with no `chunks` kwarg.

# %%
# https://docs.xarray.dev/en/stable/generated/xarray.open_zarr.html
open_zarr(zarr_path, chunks="auto").my_xda

# %% [markdown]
# ### Using datatree's `open_datatree` with `engine='zarr'`
#
# See https://xarray-datatree.readthedocs.io/en/latest/generated/datatree.open_datatree.html#datatree.open_datatree
#
# Documentation version:
#
# ```
# Datatree 0.0.14.dev5+g433f78d.d20231110 documentation
# ```

# %% [markdown]
# #### No `chunks` kwarg
#
# No chunking performed.
#
# (NOK)
#
# (!) Differs from the xarray's reference behaviour where stored chunks are used.

# %%
open_datatree(zarr_path, engine="zarr").my_xda

# %% [markdown]
# #### With `chunks='auto'`
#
# A chunk identical to the shape of the data is used.
# This means chunking is useless as there is only a single chunk representing the whole dataset
#
# (NOK)
#
# (!) Differs from the xarray's reference behaviour where stored chunks are used.
#

# %%
open_datatree(zarr_path, engine="zarr", chunks="auto").my_xda

# %% [markdown]
# #### With `chunks` kwarg (same as stored chunks)
#
# (OK)
#
# No warning is shown because given chunks correspond to the stored chunks

# %%
open_datatree(zarr_path, engine="zarr", chunks={"label": 2, "z": 4}).my_xda

# %% [markdown]
# #### With `chunks` kwarg (differing from the stored chunks)
#
# (OK)
#
# A warning is shown
#
# > UserWarning: The specified chunks separate the stored chunks along dimension "z" starting at index 5. This could degrade performance. Instead, consider rechunking after loading.

# %%
open_datatree(zarr_path, engine="zarr", chunks={"label": 999, "z": 5}).my_xda
