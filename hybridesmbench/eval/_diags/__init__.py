"""Run diagnostics."""

import importlib
import inspect
from pathlib import Path
from typing import Any

from hybridesmbench.eval._diags.base import Diagnostic, ESMValToolDiagnostic


def _is_diag(obj: Any):
    """Check if object is a diagnostic."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, Diagnostic)
        and obj is not Diagnostic
        and obj is not ESMValToolDiagnostic
    )


def _get_all_diags() -> dict[str, type]:
    """Get all available diagnostics."""
    diags: dict[str, type] = {}
    for path in Path(__file__).parent.glob("[a-z]*"):
        module_name = path.stem
        module = importlib.import_module(
            f"hybridesmbench.eval._diags.{module_name}",
        )
        all_diags = inspect.getmembers(module, _is_diag)
        if not all_diags:
            continue
        msg = (
            f"Diagnostic modules should have at most one diagnostic, found "
            f"{[d[0] for d in all_diags]} in {module.__name__}"
        )
        assert len(all_diags) < 2, msg
        diags[module_name] = all_diags[0][1]
    return diags


DIAGS = _get_all_diags()
