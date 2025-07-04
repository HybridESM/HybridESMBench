"""Load hybrid Earth system model output."""

import inspect
from typing import Any

from hybridesmbench._utils import get_classes
from hybridesmbench.eval._loaders.base import BaseICONLoader, Loader

__all__ = [
    "LOADERS",
    "BaseICONLoader",
    "Loader",
]


def _is_loader(obj: Any):
    """Check if object is a loader."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, Loader)
        and obj is not Loader
        and obj is not BaseICONLoader
    )


LOADERS: dict[str, type[Loader]] = get_classes(
    "hybridesmbench.eval._loaders", _is_loader
)
