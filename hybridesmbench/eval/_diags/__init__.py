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
        for diag_name, diag in inspect.getmembers(module, _is_diag):
            diags[diag_name] = diag
    return diags


DIAGS = _get_all_diags()
