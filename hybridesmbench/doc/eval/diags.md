# Diagnostics

## Overview

Diagnostics are classes that preprocess data and run diagnostics.
For each element of `diagnostics` supported by
:func:`hybridesmbench.eval.evaluate`, a diagnostic must be available.

The global variable :attr:`hybridesmbench.eval._diags.DIAGS` provides an
overview of all available diagnostic.

## Add support for new diagnostics

Diagnostics are subclasses of :class:`hybridesmbench.eval._diags.Diagnostic`
located in submodules of :mod:`hybridesmbench.eval._diags`.
The `name` of the diagnostic is determined by the name of its module.

For convenience, a base class
:class:`hybridesmbench.eval._diags.ESMValtoolDiagnostic` exists which provides
functionalities to run ESMValTool diagnostics.

For example, the diagnostic with name `timeseries` is located at
:mod:`hybridesmbench.eval._diags.timeseries` in the form of the class
:class:`hybridesmbench.eval._diags.timeseries.TimeSeriesDiagnostic`.
