"""Provide types for HybridESMBench."""

from typing import Literal

DiagnosticName = Literal[
    "maps",
    "portrait_plot",
    "profiles",
    "sanity_checks_1",
    "sanity_checks_2",
    "timeseries",
]

ModelType = Literal[
    "cmip",
    "icon",
]
