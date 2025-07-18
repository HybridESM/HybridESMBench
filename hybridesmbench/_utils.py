"""Provide utility functions for HybridESMBench."""

import importlib
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from esmvalcore.preprocessor import extract_levels
from iris.cube import Cube
from loguru import logger

from hybridesmbench.exceptions import HybridESMBenchException


def extract_vertical_level(var_id: str, cube: Cube, **kwargs: Any) -> Cube:
    """Extract vertical level of cube based on `var_id`.

    This interprets numbers in the `var_id` as vertical coordinate values
    (usually, pressure levels). If no numbers are present, the data is retured
    as is.

    If vertical level extraction is necessary, uses
    :func:`esmvalcore.preprocessor.extract_levels`.

    This uses

    Examples
    --------
    - `var_id=hus20000`: Extract the 20000 Pa level from `hus` (specific
      humidity).
    - `var_id=ta85000`: Extract the 85000 Pa level from `ta` (air temperature).
    - `var_id=tas`: Return `tas` as is (near-surface air temperature).

    Parameters
    ----------
    var_id:
        Variable ID.
    cube:
        Input data.
    **kwargs
        Additional keyword arguments passed to
        :func:`esmvalcore.preprocessor.extract_levels`.

    Returns
    -------
    iris.cube.Cube
        Data where the the desired vertical level is extracted.

    Raises
    ------
    ValueError
        `cube.var_name` differs from the variable name given by `var_id`.

    """
    if not var_id.startswith(cube.var_name):
        msg = (
            f"Variable ID '{var_id}' does not match `cube.var_name`, needs to "
            f"start with '{cube.var_name}'"
        )
    level_str = var_id.replace(cube.var_name, "", 1)

    # Single level data
    if not level_str:
        logger.debug(f"No level extraction necessary for variable '{var_id}'")
        return cube

    try:
        level = float(var_id.replace(cube.var_name, "", 1))
    except ValueError as exc:
        msg = (
            f"Variable ID '{var_id}' for variable '{cube.var_name}' does not "
            f"describe a valid level"
        )
        raise HybridESMBenchException(msg) from exc

    logger.debug(f"Extracting level {level} for variable '{var_id}'")
    kwargs.setdefault("scheme", "linear")
    return extract_levels(cube, level, **kwargs)


def get_classes(
    parent_module_name: str,
    predicate: Callable[[Any], bool],
) -> dict[Any, Any]:
    """Get specific classes of a module.

    Parameters
    ----------
    parent_module_name:
        Name of parent module.
    predicate:
        Only classes where `predicate` returns `True` are returned.

    Returns
    -------
    dict[str, Any]
        Desired classes of module.

    """
    classes: dict[str, type] = {}
    parent_module = importlib.import_module(parent_module_name)
    for path in Path(parent_module.__file__).parent.glob(  # type: ignore
        "[a-z]*"
    ):
        module_name = path.stem
        module = importlib.import_module(f"{parent_module_name}.{module_name}")
        all_classes = inspect.getmembers(module, predicate)
        if not all_classes:
            continue
        msg = (
            f"Modules should have at most one class in question, found "
            f"{[d[0] for d in all_classes]} in {module.__name__}"
        )
        assert len(all_classes) < 2, msg
        classes[module_name] = all_classes[0][1]
    return classes


def get_timerange(cube: Cube) -> str | None:
    """Get time range of cube."""
    if not cube.coords("time"):
        return None

    format = "%Y%m%dT%H%M%S"
    time = cube.coord("time")
    if time.has_bounds():
        first_date = time.bounds[0][0]
        last_date = time.bounds[-1][1]
    else:
        first_date = time.points[0]
        last_date = time.points[-1]
    start_date = time.units.num2date(first_date).strftime(format)
    end_date = time.units.num2date(last_date).strftime(format)
    return f"{start_date}/{end_date}"
