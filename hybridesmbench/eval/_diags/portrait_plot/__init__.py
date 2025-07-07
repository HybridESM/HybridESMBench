"""Run portrait plot diagnostic."""

from typing import Any

from iris.cube import Cube

from hybridesmbench.eval._diags.base import ESMValToolDiagnostic
from hybridesmbench.eval._loaders.base import Loader


class PortraiPlotDiagnostic(ESMValToolDiagnostic):
    """Run time series diagnostic."""

    _DIAG_CFG = {}
    _VARS = [
        {"var_name": "asr", "var_mip": "Amon"},
        {"var_name": "clivi", "var_mip": "Amon"},
        {"var_name": "clwvi", "var_mip": "Amon"},
        {"var_name": "clt", "var_mip": "Amon"},
        {"var_name": "hus", "var_mip": "Amon"},
        {"var_name": "lwcre", "var_mip": "Amon"},
        {"var_name": "lwp", "var_mip": "Amon"},
        {"var_name": "pr", "var_mip": "Amon"},
        {"var_name": "prw", "var_mip": "Amon"},
        {"var_name": "rlut", "var_mip": "Amon"},
        {"var_name": "rsut", "var_mip": "Amon"},
        {"var_name": "swcre", "var_mip": "Amon"},
        {"var_name": "ta", "var_mip": "Amon"},
        {"var_name": "tas", "var_mip": "Amon"},
        {"var_name": "tauu", "var_mip": "Amon"},
        {"var_name": "ua", "var_mip": "Amon"},
    ]

    def _preprocess(self, cube: Cube) -> Cube:
        """Preprocess input data."""
        return cube

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic."""
        pass

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        return cfg

    def _update_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Update variable metadata (in-place)."""
        return metadata
