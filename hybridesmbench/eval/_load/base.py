"""Load hybrid Earth system model output (base class)."""

import functools
import inspect
from pathlib import Path
from typing import Any

import xarray as xr
from iris.cube import Cube
from loguru import logger


class BaseLoader:
    """Load hybrid Earth system model output (base class).

    Parameters
    ----------
    path:
        Path to hybrid Earth system model output.

    """

    def __init__(self, path: Path) -> None:
        """Initialize class instance."""
        self._root_file = Path(inspect.getfile(self.__class__))
        self._path = path
        logger.debug(
            f"Initialized loader for '{self.model_type}' data located at "
            f"{path}"
        )

    def load_variable(self, var_name: str, var_mip: str) -> Cube:
        """Load single variable.

        Parameters
        ----------
        var_name:
            CMOR variable name, e.g., `"tas"`.
        var_mip:
            CMOR MIP table, e.g., `"Amon"`.

        Returns
        -------
        Cube
            Data with single variable.

        """
        logger.debug(
            f"Trying to load variable '{var_name}' from MIP '{var_mip}'"
        )
        cube = self._load_single_variable(var_name, var_mip)
        logger.debug(f"Loaded variable '{var_name}' from MIP '{var_mip}'")
        return cube

    @property
    def model_type(self) -> str:
        """Get model type of loader."""
        return self._root_file.stem

    @property
    def path(self) -> Path:
        """Get path to hybrid Earth system model output."""
        return self._path

    @functools.lru_cache
    def _load_files(self, path: str | Path, **kwargs: Any) -> xr.Dataset:
        """Load files using :func:`xarray.open_mfdataset.`

        Use LRU cache to avoid loading the same files over and over.

        """
        kwargs.setdefault("chunks", "auto")
        return xr.open_mfdataset(path, **kwargs)

    def _load_single_variable(self, var_name: str, var_mip: str) -> Cube:
        """Load single variable.

        Should be implemented by child classes.

        """
        raise NotImplementedError()
