"""Provide types for HybridESMBench."""

from typing import Literal

DiagnosticName = Literal[
    "maps",
    "portrait_plot",
    "profiles",
    "sanity_checks",
    "timeseries",
]

ModelType = Literal[
    "cmip",
    "icon",
]
