"""Load ICON hybrid Earth system model output (base class)."""

import warnings
from pathlib import Path
from typing import Any

from esmvalcore.cmor.fix import fix_data, fix_metadata
from esmvalcore.cmor.table import get_var_info
from iris.cube import Cube
from iris.warnings import IrisUserWarning
from loguru import logger
from ncdata.iris_xarray import cubes_from_xarray

from hybridesmbench.eval._load.base import BaseLoader
from hybridesmbench.exceptions import HybridESMBenchWarning


class BaseICONLoader(BaseLoader):
    """Load ICON hybrid Earth system model output (base class).

    Parameters
    ----------
    path:
        Path to ICON output.

    """

    _DATASET: str
    _VAR_TYPES: dict[str, str]

    def __init__(self, path: Path) -> None:
        """Initialize class instance."""
        super().__init__(path)

        # ICON experiment name
        self._exp = self._path.name

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
    def exp(self) -> str:
        """Get ICON experiment."""
        return self._exp

    @property
    def grid_file(self) -> Path:
        """Get path to ICON grid file."""
        return self._grid_file

    def _load_single_variable(self, var_name: str, var_mip: str) -> Cube:
        """Load single variable."""
        if var_name not in self._VAR_TYPES:
            raise ValueError(
                f"Variable '{var_name}' not supported for model type "
                f"'{self.model_type}' yet"
            )
        var_type = self._VAR_TYPES[var_name]

        # Load xarray.Dataset and convert to iris.cube.CubeList
        file_pattern = str(self.path / f"{self.exp}_{var_type}_*.nc")
        logger.debug(f"Loading files at {file_pattern}")
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
        cmor_var_info = get_var_info("ICON", var_mip, var_name)
        extra_facets: dict[str, Any] = {}
        if self.grid_file is not None:
            extra_facets["horizontal_grid"] = self.grid_file
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=IrisUserWarning)
            cube = fix_metadata(
                cubes,
                short_name=var_name,
                project="ICON",
                dataset=self._DATASET,
                mip=var_mip,
                frequency=cmor_var_info.frequency,
                **extra_facets,
            )[0]
            cube = fix_data(
                cube,
                short_name=var_name,
                project="ICON",
                dataset=self._DATASET,
                mip=var_mip,
                frequency=cmor_var_info.frequency,
                **extra_facets,
            )

        return cubes
