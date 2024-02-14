# Lack of resilience towards missing `_ARRAY_DIMENSIONS` xarray's special Zarr attribute 


```python
from pathlib import Path
import json
from typing import Any

import numpy as np
import xarray as xr
```

## \_Utilities

_This section only declares utilities functions and do not contain any additional value for the reader_



```python
# Set to True to get rich HTML representations in an interactive Notebook session
# Set to False to get textual representations ready to be converted to markdown for issue report

INTERACTIVE = False

# Convert to markdown with
# jupyter nbconvert --to markdown notebooks/datatree-zarr.ipynb
```


```python
def show(obj: Any) -> Any:
    if isinstance(obj, Path):
        if INTERACTIVE:
            return obj.resolve()
        else:
            print(obj)
    else:
        if INTERACTIVE:
            return obj
        else:
            print(obj)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)
```

## Data Creation

I create a dummy Dataset containing a single `(label, z)`-dimensional DataArray named `my_xda`.



```python
xda = xr.DataArray(
    np.arange(3 * 18).reshape(3, 18),
    coords={"label": list("abc"), "z": list(range(18))},
)
xda = xda.chunk({"label": 2, "z": 4})
show(xda)
```

    <xarray.DataArray (label: 3, z: 18)>
    dask.array<xarray-<this-array>, shape=(3, 18), dtype=int64, chunksize=(2, 4), chunktype=numpy.ndarray>
    Coordinates:
      * label    (label) <U1 'a' 'b' 'c'
      * z        (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17



```python
xds = xr.Dataset({"my_xda": xda})
show(xds)
```

    <xarray.Dataset>
    Dimensions:  (label: 3, z: 18)
    Coordinates:
      * label    (label) <U1 'a' 'b' 'c'
      * z        (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
    Data variables:
        my_xda   (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


## Data Writing

I persist the Dataset to Zarr



```python
zarr_path = Path() / "../generated/zarrounet.zarr"
xds.to_zarr(zarr_path, mode="w")
show(zarr_path)
```

    ../generated/zarrounet.zarr


## Data Initial Reading

I read successfully the Dataset



```python
show(xr.open_zarr(zarr_path).my_xda)
```

    <xarray.DataArray 'my_xda' (label: 3, z: 18)>
    dask.array<open_dataset-my_xda, shape=(3, 18), dtype=int64, chunksize=(2, 4), chunktype=numpy.ndarray>
    Coordinates:
      * label    (label) <U1 'a' 'b' 'c'
      * z        (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17


## Data Alteration


Then, I alter the Zarr by removing successively all of the `_ARRAY_DIMENSIONS` from all of the variables' `.zattrs`: `z`, `label`, `my_xda`, and try to reopen the Zarr. It is in all cases a success. ✔️



```python
# corrupt the variables' `_ARRAY_DIMENSIONS` xarray's attribute
for varname in ("z/.zattrs", "label/.zattrs", "my_xda/.zattrs"):
    zattrs_path = zarr_path / varname
    assert zattrs_path.is_file()
    zattrs_path.write_text("{}")

# Note: it has no impact, only the root .zmetdata seems to be used
```


```python
show(xr.open_zarr(zarr_path))
```

    <xarray.Dataset>
    Dimensions:  (label: 3, z: 18)
    Coordinates:
      * label    (label) <U1 'a' 'b' 'c'
      * z        (z) int64 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
    Data variables:
        my_xda   (label, z) int64 dask.array<chunksize=(2, 4), meta=np.ndarray>


However, the last alteration, which is removing the `_ARRAY_DIMENSIONS` key-value pair from one of the variables in the `.zmetadata` file present at the root of the zarr, results in an exception when reading. The error message is explicit: `KeyError: '_ARRAY_DIMENSIONS'` ❌

This means xarray cannot open any Zarr file, but only those who possess an xarray's special
private attribute, `_ARRAY_DIMENSIONS`. 

> Because of these choices, Xarray cannot read arbitrary array data, but only Zarr data with valid `_ARRAY_DIMENSIONS` 

See https://docs.xarray.dev/en/latest/internals/zarr-encoding-spec.html

In a first phase, the error message can probably be more explicit (better than a low-level `KeyError`), explaining that xarray cannot yet open arbitrary Zarr data.


```python
zmetadata_path = zarr_path / ".zmetadata"
assert zmetadata_path.is_file()
zmetadata = load_json(zmetadata_path)
zmetadata["metadata"]["z/.zattrs"] = {}
zmetadata_path.write_text(json.dumps(zmetadata, indent=4))
```




    1925




```python
show(xr.open_zarr(zarr_path))
```


    ---------------------------------------------------------------------------

    KeyError                                  Traceback (most recent call last)

    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:212, in _get_zarr_dims_and_attrs(zarr_obj, dimension_key, try_nczarr)
        210 try:
        211     # Xarray-Zarr
    --> 212     dimensions = zarr_obj.attrs[dimension_key]
        213 except KeyError as e:


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/zarr/attrs.py:73, in Attributes.__getitem__(self, item)
         72 def __getitem__(self, item):
    ---> 73     return self.asdict()[item]


    KeyError: '_ARRAY_DIMENSIONS'

    
    During handling of the above exception, another exception occurred:


    TypeError                                 Traceback (most recent call last)

    Cell In[11], line 1
    ----> 1 show(xr.open_zarr(zarr_path))


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:900, in open_zarr(store, group, synchronizer, chunks, decode_cf, mask_and_scale, decode_times, concat_characters, decode_coords, drop_variables, consolidated, overwrite_encoded_chunks, chunk_store, storage_options, decode_timedelta, use_cftime, zarr_version, chunked_array_type, from_array_kwargs, **kwargs)
        886     raise TypeError(
        887         "open_zarr() got unexpected keyword arguments " + ",".join(kwargs.keys())
        888     )
        890 backend_kwargs = {
        891     "synchronizer": synchronizer,
        892     "consolidated": consolidated,
       (...)
        897     "zarr_version": zarr_version,
        898 }
    --> 900 ds = open_dataset(
        901     filename_or_obj=store,
        902     group=group,
        903     decode_cf=decode_cf,
        904     mask_and_scale=mask_and_scale,
        905     decode_times=decode_times,
        906     concat_characters=concat_characters,
        907     decode_coords=decode_coords,
        908     engine="zarr",
        909     chunks=chunks,
        910     drop_variables=drop_variables,
        911     chunked_array_type=chunked_array_type,
        912     from_array_kwargs=from_array_kwargs,
        913     backend_kwargs=backend_kwargs,
        914     decode_timedelta=decode_timedelta,
        915     use_cftime=use_cftime,
        916     zarr_version=zarr_version,
        917 )
        918 return ds


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/api.py:573, in open_dataset(filename_or_obj, engine, chunks, cache, decode_cf, mask_and_scale, decode_times, decode_timedelta, use_cftime, concat_characters, decode_coords, drop_variables, inline_array, chunked_array_type, from_array_kwargs, backend_kwargs, **kwargs)
        561 decoders = _resolve_decoders_kwargs(
        562     decode_cf,
        563     open_backend_dataset_parameters=backend.open_dataset_parameters,
       (...)
        569     decode_coords=decode_coords,
        570 )
        572 overwrite_encoded_chunks = kwargs.pop("overwrite_encoded_chunks", None)
    --> 573 backend_ds = backend.open_dataset(
        574     filename_or_obj,
        575     drop_variables=drop_variables,
        576     **decoders,
        577     **kwargs,
        578 )
        579 ds = _dataset_from_backend_dataset(
        580     backend_ds,
        581     filename_or_obj,
       (...)
        591     **kwargs,
        592 )
        593 return ds


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:982, in ZarrBackendEntrypoint.open_dataset(self, filename_or_obj, mask_and_scale, decode_times, concat_characters, decode_coords, drop_variables, use_cftime, decode_timedelta, group, mode, synchronizer, consolidated, chunk_store, storage_options, stacklevel, zarr_version)
        980 store_entrypoint = StoreBackendEntrypoint()
        981 with close_on_error(store):
    --> 982     ds = store_entrypoint.open_dataset(
        983         store,
        984         mask_and_scale=mask_and_scale,
        985         decode_times=decode_times,
        986         concat_characters=concat_characters,
        987         decode_coords=decode_coords,
        988         drop_variables=drop_variables,
        989         use_cftime=use_cftime,
        990         decode_timedelta=decode_timedelta,
        991     )
        992 return ds


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/store.py:43, in StoreBackendEntrypoint.open_dataset(self, filename_or_obj, mask_and_scale, decode_times, concat_characters, decode_coords, drop_variables, use_cftime, decode_timedelta)
         29 def open_dataset(  # type: ignore[override]  # allow LSP violation, not supporting **kwargs
         30     self,
         31     filename_or_obj: str | os.PathLike[Any] | BufferedIOBase | AbstractDataStore,
       (...)
         39     decode_timedelta=None,
         40 ) -> Dataset:
         41     assert isinstance(filename_or_obj, AbstractDataStore)
    ---> 43     vars, attrs = filename_or_obj.load()
         44     encoding = filename_or_obj.get_encoding()
         46     vars, attrs, coord_names = conventions.decode_cf_variables(
         47         vars,
         48         attrs,
       (...)
         55         decode_timedelta=decode_timedelta,
         56     )


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/common.py:210, in AbstractDataStore.load(self)
        188 def load(self):
        189     """
        190     This loads the variables and attributes simultaneously.
        191     A centralized loading function makes it easier to create
       (...)
        207     are requested, so care should be taken to make sure its fast.
        208     """
        209     variables = FrozenDict(
    --> 210         (_decode_variable_name(k), v) for k, v in self.get_variables().items()
        211     )
        212     attributes = FrozenDict(self.get_attrs())
        213     return variables, attributes


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:519, in ZarrStore.get_variables(self)
        518 def get_variables(self):
    --> 519     return FrozenDict(
        520         (k, self.open_store_variable(k, v)) for k, v in self.zarr_group.arrays()
        521     )


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/core/utils.py:471, in FrozenDict(*args, **kwargs)
        470 def FrozenDict(*args, **kwargs) -> Frozen:
    --> 471     return Frozen(dict(*args, **kwargs))


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:520, in <genexpr>(.0)
        518 def get_variables(self):
        519     return FrozenDict(
    --> 520         (k, self.open_store_variable(k, v)) for k, v in self.zarr_group.arrays()
        521     )


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:496, in ZarrStore.open_store_variable(self, name, zarr_array)
        494 data = indexing.LazilyIndexedArray(ZarrArrayWrapper(name, self))
        495 try_nczarr = self._mode == "r"
    --> 496 dimensions, attributes = _get_zarr_dims_and_attrs(
        497     zarr_array, DIMENSION_KEY, try_nczarr
        498 )
        499 attributes = dict(attributes)
        501 # TODO: this should not be needed once
        502 # https://github.com/zarr-developers/zarr-python/issues/1269 is resolved.


    File ~/.cache/pypoetry/virtualenvs/datatree-experimentation-Sa4oWCLA-py3.10/lib/python3.10/site-packages/xarray/backends/zarr.py:222, in _get_zarr_dims_and_attrs(zarr_obj, dimension_key, try_nczarr)
        220 # NCZarr defines dimensions through metadata in .zarray
        221 zarray_path = os.path.join(zarr_obj.path, ".zarray")
    --> 222 zarray = json.loads(zarr_obj.store[zarray_path])
        223 try:
        224     # NCZarr uses Fully Qualified Names
        225     dimensions = [
        226         os.path.basename(dim) for dim in zarray["_NCZARR_ARRAY"]["dimrefs"]
        227     ]


    File ~/.pyenv/versions/3.10.12/lib/python3.10/json/__init__.py:339, in loads(s, cls, object_hook, parse_float, parse_int, parse_constant, object_pairs_hook, **kw)
        337 else:
        338     if not isinstance(s, (bytes, bytearray)):
    --> 339         raise TypeError(f'the JSON object must be str, bytes or bytearray, '
        340                         f'not {s.__class__.__name__}')
        341     s = s.decode(detect_encoding(s), 'surrogatepass')
        343 if (cls is None and object_hook is None and
        344         parse_int is None and parse_float is None and
        345         parse_constant is None and object_pairs_hook is None and not kw):


    TypeError: the JSON object must be str, bytes or bytearray, not dict

