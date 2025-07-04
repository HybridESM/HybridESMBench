# Diagnostics

## Overview

Diagnostics are classes that run diagnostics.
For each element of `diagnostics` supported by
:func:`hybridesmbench.eval.evaluate`, a diagnostic must be available.

The global variable :attr:`hybridesmbench.eval._diags.DIAGS` provides an
overview of all available diagnostic.

## Add support for new diagnostics

Diagnostics are subclasses of :class:`hybridesmbench.eval._diags.Diagnostic`
located in submodules of :mod:`hybridesmbench.eval._diags`.
The `name` of the diagnostic is determined by the name of its module.

For example, the diagnostic with name `timeseries` is located at
:mod:`hybridesmbench.eval._diags.timeseries` in the form of the class
:class:`hybridesmbench.eval._diags.timeseries.TimeSeriesDiagnostic`.
