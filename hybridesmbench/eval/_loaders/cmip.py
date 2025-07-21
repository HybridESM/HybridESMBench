"""Load CMIP6-style (i.e., CMORized) hybrid Earth system model output."""

import functools

from esmvalcore.cmor.fix import fix_data, fix_metadata
from esmvalcore.cmor.table import get_var_info
from iris.cube import Cube
from loguru import logger
from ncdata.iris_xarray import cubes_from_xarray

from hybridesmbench.eval._loaders import Loader
from hybridesmbench.exceptions import HybridESMBenchException


class CMIPLoader(Loader):
    """Load CMIP6-style (i.e., CMORized) hybrid Earth system model output.

    Parameters
    ----------
    path:
        Path to model output.

    """

    _PROJECT = "CMIP-style"
    _DATASET = "CMIP-style"

    @functools.lru_cache
    def _load_single_variable(self, var_name: str, mip_table: str) -> Cube:
        """Load single variable."""
        # First, try to find files in subdirectories called like the variable
        logger.debug(
            f"Looking for '*.nc' files in subdirectories '{var_name}' of "
            f"{self.path}"
        )
        nc_files = tuple(
            f for d in self.path.rglob(var_name) for f in d.rglob("*.nc")
        )

        # If that didn't work, try to find files which contain the variables
        # name in their file name
        if not nc_files:
            logger.debug(
                f"Looking for {var_name}_*.nc files in {self.path} (incl. "
                f"subdirectories)"
            )
            nc_files = tuple(self.path.rglob(f"{var_name}_*.nc"))

        # If that didn't work, raise exception
        if not nc_files:
            msg = (
                f"No files for variable '{var_name}' found (looked for *.nc "
                f"files in subdirectories '{var_name}' and {var_name}_*.nc "
                f"files in {self.path} [incl. subdirectories])"
            )
            raise HybridESMBenchException(msg)

        xr_ds = self._load_files(nc_files).copy()
        cubes = cubes_from_xarray(xr_ds)

        # Run automatic fixes on data (there is no specific fix for
        # self._DATASET, but the generic model-agnostic fixes will always be
        # run)
        project = "CMIP6"
        cmor_var_info = get_var_info(project, mip_table, var_name)
        cube = fix_metadata(
            cubes,
            short_name=var_name,
            project=project,
            dataset=self._DATASET,
            mip=mip_table,
            frequency=cmor_var_info.frequency,
        )[0]
        cube = fix_data(
            cube,
            short_name=var_name,
            project=project,
            dataset=self._DATASET,
            mip=mip_table,
            frequency=cmor_var_info.frequency,
        )

        return cube
