"""Run maps diagnostic."""

import warnings
from typing import Any

from esmvalcore.preprocessor import (
    climate_statistics,
    convert_units,
    regrid,
)
from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets
from iris import Constraint
from iris.cube import Cube

from hybridesmbench._utils import (
    extract_final_20_years,
    extract_vertical_level,
)
from hybridesmbench.eval._diags import ESMValToolDiagnostic
from hybridesmbench.eval._loaders import Loader


class MapsDiagnostic(ESMValToolDiagnostic):
    """Run maps diagnostic."""

    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "map": {
                "common_cbar": True,
                "fontsize": 8,
                "plot_kwargs": {
                    "default": {
                        "cmap": "Blues",
                        "levels": 12,
                    },
                },
                "plot_kwargs_bias": {
                    "extend": "neither",
                    "levels": 12,
                },
                "pyplot_kwargs": {
                    "suptitle": "{title}",
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
        cube = extract_final_20_years(cube)
        cube = extract_vertical_level(var_id, cube, coordinate="air_pressure")
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = climate_statistics(cube, operator="mean", period="full")
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
        # Special settings for cloud radiative effect variables
        cre_plot_kwargs = {
            "cmap": "bwr",
            "levels": 12,
            "norm": "centered",
        }
        for var_id in ("lwcre", "swcre"):
            cfg["plots"]["map"]["plot_kwargs"][
                self._get_alias(loader, var_id)
            ] = cre_plot_kwargs

        # Special settings for pr
        pr_plot_kwargs = {
            "cmap": "Blues",
            "extend": "max",
            "levels": 12,
        }
        cfg["plots"]["map"]["plot_kwargs"][
            self._get_alias(loader, "pr")
        ] = pr_plot_kwargs

        # Special settings for radiation variables
        rad_plot_kwargs = {
            "cmap": "YlOrRd",
            "levels": 12,
        }
        for var_id in ("rlut", "rsut"):
            cfg["plots"]["map"]["plot_kwargs"][
                self._get_alias(loader, var_id)
            ] = rad_plot_kwargs

        # Special settings for temperature variables
        temperature_plot_kwargs = {
            "cmap": "plasma",
            "levels": 12,
        }
        for var_id in ("tas", "ta20000", "ta85000"):
            cfg["plots"]["map"]["plot_kwargs"][
                self._get_alias(loader, var_id)
            ] = temperature_plot_kwargs

        # Special settings for dynamical variables
        dyn_plot_kwargs = {
            "cmap": "PuOr",
            "levels": 12,
            "norm": "centered",
        }
        for var_id in ("tauu", "ua20000", "ua85000"):
            cfg["plots"]["map"]["plot_kwargs"][
                self._get_alias(loader, var_id)
            ] = dyn_plot_kwargs

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
