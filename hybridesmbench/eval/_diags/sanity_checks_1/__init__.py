"""Run santiy checks diagnostic."""

import warnings
from typing import Any

from esmvalcore.preprocessor import (
    area_statistics,
    anomalies,
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


class SanityChecksDiagnostic(ESMValToolDiagnostic):
    """Run sanity checks diagnostic."""

    # _OBS_PLOT_KWARGS = {
    #     "color": "black",
    #     "label": "{dataset}",
    #     "linewidth": 1.0,
    #     "zorder": 2.4,
    # }
    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "timeseries": {
                # "legend_kwargs": {
                #     "loc": "upper center",
                #     "bbox_to_anchor": [0.5, -0.2],
                #     "borderaxespad": 0.0,
                # },
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
                },
                "hlines": [
                    {"y": 1.420688e+16, "color": "red", "linewidth": 2},
                    {"y": 1.128716e+16, "color": "red", "linewidth": 2},
                ],
            },
        },
    }
    _VARS = {
        # "ps": {"var_name": "ps", "mip_table": "Amon"},
        "prw": {"var_name": "prw", "mip_table": "Amon"},
        # "qep": {"var_name": "qep", "mip_table": "Amon"},
    }

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        #cube = extract_vertical_level(var_id, cube, coordinate="air_pressure")
        #if cube.var_name == "ps":
        #    cube = convert_units(cube, "kg m-2")
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "sum")
        #cube = annual_statistics(cube, "mean")
        #cube = anomalies(cube, "full")
        #if cube.var_name == "pr":
        #    cube = convert_units(cube, "mm day-1")
        
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
        cfg["plots"]["timeseries"]["plot_kwargs"][
            loader.model_name
        ] = plot_kwargs
        # cfg["plots"]["timeseries"]["hline"
        # ] = [{"y": 1.420688e+16, "color": "red"}]
        return cfg

    def _update_metadata(
        self,
        var_id: str,
        loader: Loader,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        better_long_name = self._get_better_long_name(
            var_id, metadata["short_name"], metadata["long_name"]
        )
        metadata["title"] = f"Global Sum of {better_long_name}"
        return metadata