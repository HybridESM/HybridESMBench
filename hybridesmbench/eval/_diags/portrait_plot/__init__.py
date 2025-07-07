"""Run portrait plot diagnostic."""

from typing import Any

from iris.cube import Cube

from hybridesmbench.eval._diags.base import ESMValToolDiagnostic
from hybridesmbench.eval._loaders.base import Loader


class PortraiPlotDiagnostic(ESMValToolDiagnostic):
    """Run time series diagnostic."""

    _DIAG_CFG = {}
    _VARS = {
        "asr": {"var_name": "asr", "var_mip": "Amon"},
        "clivi": {"var_name": "clivi", "var_mip": "Amon"},
        "clwvi": {"var_name": "clwvi", "var_mip": "Amon"},
        "clt": {"var_name": "clt", "var_mip": "Amon"},
        "hus400": {"var_name": "hus", "var_mip": "Amon"},
        "lwcre": {"var_name": "lwcre", "var_mip": "Amon"},
        "lwp": {"var_name": "lwp", "var_mip": "Amon"},
        "pr": {"var_name": "pr", "var_mip": "Amon"},
        "prw": {"var_name": "prw", "var_mip": "Amon"},
        "rlut": {"var_name": "rlut", "var_mip": "Amon"},
        "rsut": {"var_name": "rsut", "var_mip": "Amon"},
        "swcre": {"var_name": "swcre", "var_mip": "Amon"},
        "ta200": {"var_name": "ta", "var_mip": "Amon"},
        "ta850": {"var_name": "ta", "var_mip": "Amon"},
        "tas": {"var_name": "tas", "var_mip": "Amon"},
        "tauu": {"var_name": "tauu", "var_mip": "Amon"},
        "ua200": {"var_name": "ua", "var_mip": "Amon"},
        "ua850": {"var_name": "ua", "var_mip": "Amon"},
    }

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        return cube

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic."""
        return

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        return cfg

    def _update_metadata(
        self,
        var_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update variable metadata (in-place)."""
        return metadata
