"""Run diagnostics."""

import contextlib
import importlib
from pathlib import Path


def _get_all_diags() -> dict[str, type]:
    """Get all available diagnostics."""
    diags: dict[str, type] = {}
    for path in Path(__file__).parent.glob("[a-z]*"):
        module_name = path.stem
        module = importlib.import_module(
            f"hybridesmbench.eval._diags.{module_name}",
        )
        with contextlib.suppress(AttributeError):
            diags[module_name] = module.Diagnostic
    return diags


DIAGS = _get_all_diags()
