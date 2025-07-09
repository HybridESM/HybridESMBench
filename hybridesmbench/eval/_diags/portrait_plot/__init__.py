"""Run portrait plot diagnostic."""

from typing import Any

import iris
from esmvalcore.preprocessor import (
    climate_statistics,
    regrid,
)
from iris import Constraint
from iris.cube import Cube

from hybridesmbench._utils import extract_vertical_level
from hybridesmbench.eval._diags.base import ESMValToolDiagnostic
from hybridesmbench.eval._loaders.base import Loader


class PortraiPlotDiagnostic(ESMValToolDiagnostic):
    """Run time series diagnostic."""

    _DIAG_CFG = {}
    _VARS = {
        # "asr": {"var_name": "asr", "mip_table": "Amon"},
        "clivi": {"var_name": "clivi", "mip_table": "Amon"},
        "clwvi": {"var_name": "clwvi", "mip_table": "Amon"},
        "clt": {"var_name": "clt", "mip_table": "Amon"},
        "hus400": {"var_name": "hus", "mip_table": "Amon"},
        # "lwcre": {"var_name": "lwcre", "mip_table": "Amon"},
        # "lwp": {"var_name": "lwp", "mip_table": "Amon"},
        "pr": {"var_name": "pr", "mip_table": "Amon"},
        "prw": {"var_name": "prw", "mip_table": "Amon"},
        "rlut": {"var_name": "rlut", "mip_table": "Amon"},
        "rsut": {"var_name": "rsut", "mip_table": "Amon"},
        # "swcre": {"var_name": "swcre", "mip_table": "Amon"},
        "ta200": {"var_name": "ta", "mip_table": "Amon"},
        "ta850": {"var_name": "ta", "mip_table": "Amon"},
        "tas": {"var_name": "tas", "mip_table": "Amon"},
        "tauu": {"var_name": "tauu", "mip_table": "Amon"},
        "ua200": {"var_name": "ua", "mip_table": "Amon"},
        "ua850": {"var_name": "ua", "mip_table": "Amon"},
    }

    def _get_ref_cube(self, var_id: str) -> Cube:
        """Get reference data for calculation of distance metrics."""
        ref_dir = self._data_dir / "references" / var_id
        ref_paths = list(ref_dir.glob("*.nc"))
        if len(ref_paths) != 1:
            raise ValueError(
                f"Expected exactly 1 reference dataset for variable "
                f"'{var_id}' located at {ref_dir}/*.nc, got {len(ref_paths)}"
            )
        return iris.load_cube(ref_paths[0])

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(
            Constraint(time=lambda c: 1979 <= c.point.year <= 1979)
        )
        cube = extract_vertical_level(var_id, cube)
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = climate_statistics(cube, operator="mean", period="month")
        self._get_ref_cube(var_id)

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
