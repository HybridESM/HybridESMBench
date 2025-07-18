"""Evaluate hybrid Earth system model simulations."""

import warnings
from collections.abc import Iterable
from pathlib import Path

from hybridesmbench.eval._diags import DIAGS
from hybridesmbench.eval._loaders import LOADERS
from hybridesmbench.exceptions import HybridESMBenchWarning
from hybridesmbench.typing import DiagnosticName, ModelType

__all__ = [
    "evaluate",
]


def evaluate(
    path: str | Path,
    model_type: ModelType,
    work_dir: str | Path,
    *,
    model_name: str | None = None,
    diagnostics: Iterable[DiagnosticName] | None = None,
    fail_on_diag_error: bool = True,
) -> dict[str, Path | None]:
    """Evaluate hybrid Earth system model output.

    Parameters
    ----------
    path:
        Path to hybrid Earth system model output.
    model_type:
        Hybrid Earth system model type.
    work_dir:
        Work directory where files created by the diagnostics are stored.
    model_name:
        Custom name for the hybrid Earth system model used to identify the
        model in the output. By default, use a name infered from `model_type`
        and `path`.
    diagnostics:
        Diagnostics to run. If `None`, run all available diagnostics.
    fail_on_diag_error:
        If `True`, raise exception if a diagnostic returns an error. If
        `False`, only raise a warning.

    Returns
    -------
    dict[str, Path | None]
        Diagnostic output directories. If diagnostic failed to run and
        `fail_on_diag_error=False`, return `None` for that diagnostic.

    """
    path = Path(path)
    work_dir = Path(work_dir)

    if model_type not in LOADERS:
        msg = (
            f"Got invalid model_type '{model_type}', must be one of "
            f"{list(LOADERS)}"
        )
        raise ValueError(msg)
    loader = LOADERS[model_type](path, model_name=model_name)

    if diagnostics is None:
        diagnostics = list(DIAGS)
    for diag_name in diagnostics:
        if diag_name not in DIAGS:
            msg = (
                f"Got invalid diagnostic '{diag_name}', must be one of "
                f"{list(DIAGS)}"
            )
            raise ValueError(msg)

    output: dict[str, Path | None] = {}
    for diag_name in diagnostics:
        diagnostic = DIAGS[diag_name](work_dir)
        try:
            output_dir: Path | None = diagnostic.run(loader)
        except Exception as exc:
            if fail_on_diag_error:
                raise
            msg = (
                f"Diagnostic '{diag_name}' failed to run on '{model_type}' "
                f"data located at {path}: {exc}"
            )
            warnings.warn(msg, HybridESMBenchWarning, stacklevel=2)
            output_dir = None
        output[diag_name] = output_dir

    return output
