"""Run profiles diagnostic."""

import warnings
from typing import Any

from esmvalcore.preprocessor import (
    climate_statistics,
    extract_levels,
    regrid,
    zonal_statistics,
)
from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets
from iris import Constraint
from iris.cube import Cube

from hybridesmbench._utils import PLEV_19_LEVELS, extract_final_20_years
from hybridesmbench.eval._diags import ESMValToolDiagnostic
from hybridesmbench.eval._loaders import Loader


class ProfilesDiagnostic(ESMValToolDiagnostic):
    """Run profiles diagnostic."""

    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "zonal_mean_profile": {
                "common_cbar": True,
                "fontsize": 8,
                "plot_kwargs": {
                    "default": {
                        "cmap": "plasma",
                        "levels": 12,
                    },
                },
                "plot_kwargs_bias": {
                    "levels": 12,
                },
                "pyplot_kwargs": {
                    "suptitle": "{title}",
                },
            },
        },
    }
    _VARS = {
        "hus": {"var_name": "hus", "mip_table": "Amon"},
        "ta": {"var_name": "ta", "mip_table": "Amon"},
        "ua": {"var_name": "ua", "mip_table": "Amon"},
    }

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = extract_final_20_years(cube)
        cube = extract_levels(
            cube,
            PLEV_19_LEVELS,
            "linear",
            coordinate="air_pressure",
        )
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = zonal_statistics(cube, "mean")
        cube = climate_statistics(cube, operator="mean", period="full")
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
        # Special settings for hus
        hus_plot_kwargs = {
            "cmap": "Blues",
            "norm": "log",
            "levels": [
                1.0e-07,
                3.16e-07,
                1.0e-06,
                3.16e-06,
                1.0e-05,
                3.16e-05,
                0.0001,
                0.000316,
                0.001,
                0.00316,
                0.01,
                0.0316,
                0.1,
            ],
        }
        cfg["plots"]["zonal_mean_profile"]["plot_kwargs"][
            self._get_alias(loader, "hus")
        ] = hus_plot_kwargs

        # Special settings for ua
        ua_plot_kwargs = {
            "cmap": "PuOr",
            "norm": "centered",
        }
        cfg["plots"]["zonal_mean_profile"]["plot_kwargs"][
            self._get_alias(loader, "ua")
        ] = ua_plot_kwargs

        return cfg

    def _update_metadata(
        self,
        var_id: str,
        loader: Loader,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        metadata["alias"] = self._get_alias(loader, var_id)
        metadata["title"] = self._get_better_long_name(
            var_id, metadata["short_name"], metadata["long_name"]
        )
        return metadata

    @staticmethod
    def _get_alias(loader: Loader, var_id: str):
        """Get alias"""
        return f"{loader.model_name} [{var_id}]"
