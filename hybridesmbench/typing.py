"""Provide types for HybridESMBench."""

from typing import Literal

DiagnosticName = Literal[
    "maps",
    "portrait_plot",
    "profiles",
    "timeseries",
]

ModelType = Literal[
    "cmip",
    "icon",
]
