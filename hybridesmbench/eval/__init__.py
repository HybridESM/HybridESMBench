"""Evaluate hybrid Earth system model simulations."""

import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from hybridesmbench.eval._diags import DIAGS
from hybridesmbench.eval._loaders import LOADERS
from hybridesmbench.exceptions import HybridESMBenchWarning

__all__ = [
    "evaluate",
]


def evaluate(
    path: str | Path,
    model_type: Literal["icon"],
    work_dir: str | Path,
    diagnostics: Iterable[str] | None = None,
) -> dict[str, Path | None]:
    """Evaluate hybrid Earth system model output.

    Parameters
    ----------
    path:
        Path to hybrid Earth system model output.
    model_type:
        _description_
    work_dir:
        _description_
    diagnostics:
        Diagnostics to run. If `None`, run all available diagnostics.

    Returns
    -------
    dict[str, Path | None]
        Diagnostic output directories. If diagnostic failed to run, return
        `None` for that diagnostic.

    """
    path = Path(path)
    work_dir = Path(work_dir)

    if model_type not in LOADERS:
        msg = (
            f"Got invalid model_type '{model_type}', must be one of "
            f"{list(LOADERS)}"
        )
        raise ValueError(msg)

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
            output_dir: Path | None = diagnostic.run(path, model_type)
        except Exception as exc:
            msg = (
                f"Diagnostic '{diag_name}' failed to run on data {path}: {exc}"
            )
            warnings.warn(msg, HybridESMBenchWarning, stacklevel=2)
            output_dir = None
        output[diag_name] = output_dir

    return output
