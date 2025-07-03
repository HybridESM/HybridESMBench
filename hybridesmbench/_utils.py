"""Provide utility functions for HybridESMBench."""

import importlib
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any


def get_classes(
    parent_module_name: str,
    predicate: Callable[[Any], bool],
) -> dict[str, type]:
    """Get classes of a module."""
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
