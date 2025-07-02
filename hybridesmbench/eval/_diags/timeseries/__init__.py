"""Provide time series diagnostic."""

import warnings
from typing import Any

from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets

from hybridesmbench.eval._diags.base import Diagnostic as BaseDiagnostic


class Diagnostic(BaseDiagnostic):
    """Setup time series diagnostic."""

    _OBS_PLOT_KWARGS = {
        "color": "black",
        "label": "{dataset}",
        "linewidth": 1.0,
        "zorder": 2.4,
    }
    _SETTINGS = {
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
                    "bbox_to_anchor": [0.5, -0.4],
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
                    "OBS_GPCP-SG": _OBS_PLOT_KWARGS,
                    "OBS_HadCRUT5": _OBS_PLOT_KWARGS,
                    "OBS6": _OBS_PLOT_KWARGS,
                    "native6": _OBS_PLOT_KWARGS,
                },
            },
        },
    }
    _VARS = [
        {"mip": "Amon", "short_name": "tas"},
    ]

    def _run_diag_function(self, cfg: dict[str, Any]) -> None:
        """Run diagnostic."""
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
