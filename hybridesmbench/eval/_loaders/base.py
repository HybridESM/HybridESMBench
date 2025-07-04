"""Load hybrid Earth system model output (base class)."""

import functools
import inspect
import warnings
from pathlib import Path
from typing import Any

import xarray as xr
from esmvalcore.cmor.fix import fix_data, fix_metadata
from esmvalcore.cmor.table import get_var_info
from iris.cube import Cube
from iris.warnings import IrisUserWarning
from loguru import logger
from ncdata.iris_xarray import cubes_from_xarray

from hybridesmbench.exceptions import HybridESMBenchWarning


class Loader:
    """Load hybrid Earth system model output (base class).

    Parameters
    ----------
    path:
        Path to hybrid Earth system model output.

    """

    _DATASET: str
    _PROJECT: str

    def __init__(self, path: Path) -> None:
        """Initialize class instance."""
        self._root_file = Path(inspect.getfile(self.__class__))
        self._path = path
        self._exp = path.name
        logger.debug(
            f"Initialized loader for '{self.model_type}' data located at "
            f"{path}"
        )

    def get_metadata(self, var_name: str, mip_table: str) -> dict[str, Any]:
        """Get variable metadata.

        Parameters
        ----------
        var_name:
            CMOR variable name, e.g., `"tas"`.
        mip_table:
            CMOR MIP table, e.g., `"Amon"`.

        Returns
        -------
        dict[str, Any]
            Variable metadata.

        """
        metadata: dict[str, Any] = {}

        # OBS6 has basically CMIP6 variables plus all custom variables
        cmor_var_info = get_var_info("OBS6", mip_table, var_name)
        msg = f"Invalid variable: '{var_name}' (MIP table: {mip_table})"
        assert cmor_var_info is not None, msg

        metadata["alias"] = self.alias
        metadata["dataset"] = self._DATASET
        metadata["exp"] = self.exp
        metadata["frequency"] = cmor_var_info.frequency
        metadata["long_name"] = cmor_var_info.long_name
        metadata["mip"] = mip_table
        metadata["modeling_realm"] = cmor_var_info.modeling_realm
        metadata["project"] = self._PROJECT
        metadata["short_name"] = var_name
        metadata["standard_name"] = cmor_var_info.standard_name
        metadata["units"] = cmor_var_info.units
        metadata["variable_group"] = var_name

        return metadata

    def load_variable(self, var_name: str, mip_table: str) -> Cube:
        """Load single variable.

        Parameters
        ----------
        var_name:
            CMOR variable name, e.g., `"tas"`.
        mip_table:
            CMOR MIP table, e.g., `"Amon"`.

        Returns
        -------
        Cube
            Data with single variable.

        """
        logger.debug(
            f"Loading variable '{var_name}' from MIP table '{mip_table}'"
        )
        cube = self._load_single_variable(var_name, mip_table)
        logger.debug(
            f"Loaded variable '{var_name}' from MIP table'{mip_table}'"
        )
        return cube

    @property
    def alias(self) -> str:
        """Get model alias."""
        return self.model_type.upper()

    @property
    def exp(self) -> str:
        """Get ICON experiment."""
        return self._exp

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

    def _load_single_variable(self, var_name: str, mip_table: str) -> Cube:
        """Load single variable.

        Should be implemented by child classes.

        """
        raise NotImplementedError()


class BaseICONLoader(Loader):
    """Load ICON hybrid Earth system model output (base class).

    Parameters
    ----------
    path:
        Path to ICON output.

    """

    _PROJECT = "ICON"
    _VAR_TYPES: dict[str, str]

    def __init__(self, path: Path) -> None:
        """Initialize class instance."""
        super().__init__(path)

        # ICON grid file
        grid_file_pattern = "icon_grid_*.nc"
        grid_files = list(self.path.glob(grid_file_pattern))
        if not grid_files:
            msg = (
                f"No ICON grid file available (searched for "
                f"{self.path / grid_file_pattern})"
            )
            raise ValueError(msg)
        if len(grid_files) > 1:
            msg = (
                f"Multiple ICON grid files available (searched for "
                f"{self.path / grid_file_pattern}), choosing first one: "
                f"{grid_files[0]}"
            )
            warnings.warn(msg, HybridESMBenchWarning, stacklevel=2)
        self._grid_file = grid_files[0]

    @property
    def alias(self) -> str:
        """Get model alias."""
        return f"{self._DATASET} ({self.exp})"

    @property
    def grid_file(self) -> Path:
        """Get path to ICON grid file."""
        return self._grid_file

    def _load_single_variable(self, var_name: str, mip_table: str) -> Cube:
        """Load single variable."""
        msg = (
            f"Invalid variable '{var_name}' for model type '{self.model_type}'"
        )
        assert var_name in self._VAR_TYPES, msg
        var_type = self._VAR_TYPES[var_name]

        # Load xarray.Dataset and convert to iris.cube.CubeList
        file_pattern = str(self.path / f"{self.exp}_{var_type}_*.nc")
        logger.debug(f"Loading files {file_pattern}")
        xr_ds = self._load_files(file_pattern)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=IrisUserWarning)
            cubes = cubes_from_xarray(xr_ds)

        # Remove lat/lon information from cubes (we will use the ones given by
        # the grid file which is much safer)
        for cube in cubes:
            for coord_name in ("latitude", "longitude"):
                if cube.coords(coord_name):
                    cube.remove_coord(coord_name)

        # Run ESMValCore fixes on the data to "CMORize" it
        cmor_var_info = get_var_info(self._PROJECT, mip_table, var_name)
        extra_facets: dict[str, Any] = {
            "horizontal_grid": self.grid_file,
        }
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=IrisUserWarning)
            cube = fix_metadata(
                cubes,
                short_name=var_name,
                project=self._PROJECT,
                dataset=self._DATASET,
                mip=mip_table,
                frequency=cmor_var_info.frequency,
                **extra_facets,
            )[0]
            cube = fix_data(
                cube,
                short_name=var_name,
                project=self._PROJECT,
                dataset=self._DATASET,
                mip=mip_table,
                frequency=cmor_var_info.frequency,
                **extra_facets,
            )

        return cube
