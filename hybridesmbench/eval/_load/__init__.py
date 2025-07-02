"""Load hybrid Earth system model output."""

import contextlib
import importlib
from pathlib import Path


def _get_all_loaders() -> dict[str, type]:
    """Get all available loaders."""
    loaders: dict[str, type] = {}
    for path in Path(__file__).parent.glob("[a-z]*.py"):
        module_name = path.stem
        module = importlib.import_module(
            f"hybridesmbench.eval._load.{module_name}",
        )
        with contextlib.suppress(AttributeError):
            loaders[module_name] = module.Loader
    return loaders


LOADERS = _get_all_loaders()
