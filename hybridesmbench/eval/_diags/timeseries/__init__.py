"""Run time series diagnostic."""

import warnings
from typing import Any

from esmvalcore.preprocessor import (
    annual_statistics,
    area_statistics,
    convert_units,
    regrid,
)
from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets
from iris import Constraint
from iris.cube import Cube

from hybridesmbench._utils import extract_vertical_level
from hybridesmbench.eval._diags import ESMValToolDiagnostic
from hybridesmbench.eval._loaders import Loader


class TimeSeriesDiagnostic(ESMValToolDiagnostic):
    """Run time series diagnostic."""

    _OBS_PLOT_KWARGS = {
        "color": "black",
        "label": "{dataset}",
        "linewidth": 1.0,
        "zorder": 2.4,
    }
    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "figure_kwargs": {
            "figsize": [7, 5],
        },
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "timeseries": {
                "annual_mean_kwargs": False,
                "legend_kwargs": {
                    "loc": "upper center",
                    "bbox_to_anchor": [0.5, -0.2],
                    "borderaxespad": 0.0,
                },
                "pyplot_kwargs": {
                    "title": "{title}",
                },
                "plot_kwargs": {
                    "default": {
                        "color": "lightgray",
                        "label": None,
                        "linewidth": 0.75,
                        "zorder": 1.0,
                    },
                    "CMIP6_CESM2": {
                        "label": "{project}",  # only show 'CMIP6' label once
                    },
                    "OBS": _OBS_PLOT_KWARGS,
                    "OBS_CERES-EBAF": _OBS_PLOT_KWARGS,
                    "OBS_ESACCI-CLOUD": _OBS_PLOT_KWARGS,
                    "OBS_GPCP-SG": _OBS_PLOT_KWARGS,
                    "OBS_HadCRUT5": _OBS_PLOT_KWARGS,
                    "OBS6": _OBS_PLOT_KWARGS,
                    "OBS6_ESACCI-WATERVAPOUR": _OBS_PLOT_KWARGS,
                    "native6": _OBS_PLOT_KWARGS,
                    "native6_ERA5": _OBS_PLOT_KWARGS,
                },
            },
        },
    }
    _VARS = {
        # "asr": {"var_name": "asr", "mip_table": "Amon"},
        "clivi": {"var_name": "clivi", "mip_table": "Amon"},
        "clwvi": {"var_name": "clwvi", "mip_table": "Amon"},
        "clt": {"var_name": "clt", "mip_table": "Amon"},
        "hus40000": {"var_name": "hus", "mip_table": "Amon"},
        # "lwcre": {"var_name": "lwcre", "mip_table": "Amon"},
        # "lwp": {"var_name": "lwp", "mip_table": "Amon"},
        "pr": {"var_name": "pr", "mip_table": "Amon"},
        "prw": {"var_name": "prw", "mip_table": "Amon"},
        "rlut": {"var_name": "rlut", "mip_table": "Amon"},
        "rsut": {"var_name": "rsut", "mip_table": "Amon"},
        "rtmt": {"var_name": "rtmt", "mip_table": "Amon"},
        # "swcre": {"var_name": "swcre", "mip_table": "Amon"},
        "ta20000": {"var_name": "ta", "mip_table": "Amon"},
        "ta85000": {"var_name": "ta", "mip_table": "Amon"},
        "tas": {"var_name": "tas", "mip_table": "Amon"},
        "tauu": {"var_name": "tauu", "mip_table": "Amon"},
        "ua20000": {"var_name": "ua", "mip_table": "Amon"},
        "ua85000": {"var_name": "ua", "mip_table": "Amon"},
    }

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = extract_vertical_level(var_id, cube, coordinate="air_pressure")
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "mean")
        cube = annual_statistics(cube, "mean")
        if cube.var_name == "pr":
            cube = convert_units(cube, "mm day-1")
        return cube

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic."""
        # TODO: this entire block can be replaced with main(cfg) in
        # ESMValTool v2.13.0
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Using DEFAULT_SPHERICAL_EARTH_RADIUS",
                category=UserWarning,
                module="iris",
            )
            MultiDatasets(cfg).compute()

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        plot_kwargs = {
            "color": "C0",
            "label": "{alias}",
            "linewidth": 1.25,
            "zorder": 2.5,
        }
        cfg["plots"]["timeseries"]["plot_kwargs"][loader.alias] = plot_kwargs
        return cfg

    def _update_metadata(
        self,
        var_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        better_long_name = self._get_better_long_name(
            var_id, metadata["short_name"], metadata["long_name"]
        )
        metadata["title"] = f"Global Mean {better_long_name}"
        return metadata
