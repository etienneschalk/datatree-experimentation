```python
import xarray as xr
import pandas as pd 
import numpy as np
```

## Reproduce the bug

Example taken from [DataArray.resample](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.resample.html), adapted to name the dimension `valid_time`


```python
xda = xr.DataArray(
    np.linspace(0, 11, num=12),
    coords={"valid_time":
        pd.date_range(
            "1999-12-15",
            periods=12,
            freq=pd.DateOffset(months=1),
        )
    },
)
print(xda)
```


```python
try:
    data_per_day = xda.resample(valid_time="1D").interpolate("polynomial")
except ValueError as err:
    assert str(err) == "order is required when method=polynomial"
```


```python
try:
    data_per_day = xda.resample(valid_time="1D").interpolate(kind="polynomial", order=3)
except TypeError as err:
    assert (
        str(err) == "Resample.interpolate() got an unexpected keyword argument 'order'"
    )
```

## Technical Analysis

First error message

> "order is required when method=polynomial"

Source: https://github.com/pydata/xarray/blob/main/xarray/core/missing.py#L153

It seems that the `method` argument becomes the `order` one when `method == 'polynomial'`. It is unclear to me what the `order` argument is supposed to contain. Maybe @jhamman have an idea? This seems to have been introduced in https://github.com/pydata/xarray/pull/1640

Second error message:

> "Resample.interpolate() got an unexpected keyword argument 'order'"

Check https://docs.xarray.dev/en/stable/generated/xarray.core.resample.DataArrayResample.interpolate.html

Source: https://github.com/pydata/xarray/blob/main/xarray/core/resample.py#L143-L171

We can see that the function signature only allows for a single `kind` keyword, hence the `TypeError: Resample.interpolate() got an unexpected keyword argument 'order'` is the direct consequence.

It uses [interp1d](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html). :warning: This function is declared as legacy, so maybe xarray should move away from its use?


## `xr.show_versions()`


```python
import warnings

warnings.filterwarnings("ignore")
xr.show_versions()
```
