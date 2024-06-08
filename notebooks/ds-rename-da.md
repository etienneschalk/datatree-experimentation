```python
import xarray as xr
```

https://docs.xarray.dev/en/stable/generated/xarray.DataArray.name.html


```python
xds = xr.Dataset({"a": xr.DataArray([1])})
print(xds)
```

    <xarray.Dataset>
    Dimensions:  (dim_0: 1)
    Dimensions without coordinates: dim_0
    Data variables:
        a        (dim_0) int64 1



```python
print(xds["a"])
```

    <xarray.DataArray 'a' (dim_0: 1)>
    array([1])
    Dimensions without coordinates: dim_0



```python
xds["a"].name = "toto"
```


```python
print(xds["a"])
```

    <xarray.DataArray 'a' (dim_0: 1)>
    array([1])
    Dimensions without coordinates: dim_0



```python
xda = xds["a"]
xda.name = "toto"
print(xda)
```

    <xarray.DataArray 'toto' (dim_0: 1)>
    array([1])
    Dimensions without coordinates: dim_0



```python
print(xds)
```

    <xarray.Dataset>
    Dimensions:  (dim_0: 1)
    Dimensions without coordinates: dim_0
    Data variables:
        a        (dim_0) int64 1

