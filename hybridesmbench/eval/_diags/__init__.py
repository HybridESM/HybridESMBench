"""Run diagnostics."""

import inspect
from typing import Any

from hybridesmbench._utils import get_classes
from hybridesmbench.eval._diags.base import Diagnostic, ESMValToolDiagnostic


def _is_diag(obj: Any):
    """Check if object is a diagnostic."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, Diagnostic)
        and obj is not Diagnostic
        and obj is not ESMValToolDiagnostic
    )


def _is_esmvaltool_diag(obj: Any):
    """Check if object is an ESMValTool diagnostic."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, ESMValToolDiagnostic)
        and obj is not ESMValToolDiagnostic
    )


DIAGS = get_classes("hybridesmbench.eval._diags", _is_diag)
ESMVALTOOL_DIAGS = get_classes(
    "hybridesmbench.eval._diags", _is_esmvaltool_diag
)
