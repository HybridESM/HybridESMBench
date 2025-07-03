"""Provide utility functions for HybridESMBench."""

import importlib
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from iris.cube import Cube


def get_classes(
    parent_module_name: str,
    predicate: Callable[[Any], bool],
) -> dict[str, Any]:
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
