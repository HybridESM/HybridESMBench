"""Load hybrid Earth system model output."""

import importlib
import inspect
from pathlib import Path
from typing import Any

from hybridesmbench.eval._loaders.base import BaseICONLoader, Loader


def _is_loader(obj: Any):
    """Check if object is a loader."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, Loader)
        and obj is not Loader
        and obj is not BaseICONLoader
    )


def _get_all_loaders() -> dict[str, type]:
    """Get all available loaders."""
    loaders: dict[str, type] = {}
    for path in Path(__file__).parent.glob("[a-z]*"):
        module_name = path.stem
        module = importlib.import_module(
            f"hybridesmbench.eval._loaders.{module_name}",
        )
        all_loaders = inspect.getmembers(module, _is_loader)
        if not all_loaders:
            continue
        msg = (
            f"Loader modules should have at most one loader, found "
            f"{[d[0] for d in all_loaders]} in {module.__name__}"
        )
        assert len(all_loaders) < 2, msg
        loaders[module_name] = all_loaders[0][1]
    return loaders


LOADERS = _get_all_loaders()
