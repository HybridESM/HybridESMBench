# Loaders

## Overview

Loaders are classes that load data from the file system into CF- and
CMOR-compliant data cubes of type :class:`iris.cube.Cube`.
For each `model_type` supported by :func:`hybridesmbench.eval.evaluate`, a
loader must be available.

The global variable :attr:`hybridesmbench.eval._loaders.LOADERS` provides an
overview of all available loaders.

## Add support for new loaders

Loaders are subclasses of :class:`hybridesmbench.eval._loaders.Loader` located
in submodules of :mod:`hybridesmbench.eval._loaders`.
The `model_type` of the loader is determined by the name of its module.

For example, the loader for ICON data (`model_type = 'icon'`) is located at
:mod:`hybridesmbench.eval._loaders.icon` in the form of the class
:class:`hybridesmbench.eval._loaders.icon.ICONLoader`.
