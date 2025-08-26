"""Run portrait plot diagnostic."""

from typing import Any

import iris
from esmvalcore.preprocessor import (
    climate_statistics,
    distance_metric,
    regrid,
)
from esmvaltool.diag_scripts.portrait_plot import main
from iris import Constraint
from iris.cube import Cube

from hybridesmbench._utils import (
    extract_final_20_years,
    extract_vertical_level,
)
from hybridesmbench.eval._diags.base import ESMValToolDiagnostic
from hybridesmbench.exceptions import HybridESMBenchException
from hybridesmbench.eval._loaders import Loader


class PortraiPlotDiagnostic(ESMValToolDiagnostic):
    """Run time series diagnostic."""

    _DIAG_CFG = {
        "x_by": "alias",
        "y_by": "variable_group",
        "group_by": "project",
        "normalize": "centered_median",
        "nan_color": None,
        "matplotlib_rc_params": {
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
        },
        "plot_kwargs": {
            "vmin": -0.5,
            "vmax": 0.5,
        },
        "cbar_kwargs": {
            "label": "Relative RMSE",
            "extend": "both",
        },
        "plot_legend": False,
    }
    _VARS = {
        "asr": {"var_name": "asr", "mip_table": "Amon"}, #
        "clivi": {"var_name": "clivi", "mip_table": "Amon"},
        "clwvi": {"var_name": "clwvi", "mip_table": "Amon"},
        "clt": {"var_name": "clt", "mip_table": "Amon"},
        "hus40000": {"var_name": "hus", "mip_table": "Amon"},
        "lwcre": {"var_name": "lwcre", "mip_table": "Amon"}, #
        "lwp": {"var_name": "lwp", "mip_table": "Amon"}, #
        "pr": {"var_name": "pr", "mip_table": "Amon"},
        "prw": {"var_name": "prw", "mip_table": "Amon"},
        "rlut": {"var_name": "rlut", "mip_table": "Amon"},
        "rsut": {"var_name": "rsut", "mip_table": "Amon"},
        "swcre": {"var_name": "swcre", "mip_table": "Amon"}, #
        "ta20000": {"var_name": "ta", "mip_table": "Amon"},
        "ta85000": {"var_name": "ta", "mip_table": "Amon"},
        "tas": {"var_name": "tas", "mip_table": "Amon"},
        "tauu": {"var_name": "tauu", "mip_table": "Amon"},
        "ua20000": {"var_name": "ua", "mip_table": "Amon"},
        "ua85000": {"var_name": "ua", "mip_table": "Amon"},
    }

    def _get_ref_cube(self, var_id: str) -> Cube:
        """Get reference data for calculation of distance metrics."""
        ref_dir = self._data_dir / "references" / var_id
        ref_paths = list(ref_dir.glob("*.nc"))
        if len(ref_paths) != 1:
            raise HybridESMBenchException(
                f"Expected exactly 1 reference dataset for variable "
                f"'{var_id}' located at {ref_dir}/*.nc, got {len(ref_paths)}"
            )
        return iris.load_cube(ref_paths[0])

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = extract_final_20_years(cube)
        cube = extract_vertical_level(var_id, cube, coordinate="air_pressure")
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = climate_statistics(cube, operator="mean", period="month")
        ref_cube = self._get_ref_cube(var_id)
        cube = distance_metric([cube], "weighted_rmse", reference=ref_cube)[0]
        return cube

    def _update_metadata(
        self,
        var_id: str,
        loader: Loader,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        metadata["project"] = "HybridESM"
        return metadata

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic."""
        return main(cfg)
