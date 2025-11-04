"""Provide types for HybridESMBench."""

from typing import Literal

DiagnosticName = Literal[
    "maps",
    "portrait_plot",
    "profiles",
    "sanity_checks_sum",
    "sanity_checks_mean",
    "timeseries",
]

ModelType = Literal[
    "cmip",
    "icon",
    "climsim",
]
