"""Run diagnostics (base class)."""

import datetime
import inspect
import warnings
from pathlib import Path
from typing import Any

import iris
import yaml
from iris.cube import Cube
from loguru import logger

from hybridesmbench._utils import get_timerange
from hybridesmbench.eval._loaders import Loader
from hybridesmbench.exceptions import (
    HybridESMBenchException,
    HybridESMBenchWarning,
)


class Diagnostic:
    """Run diagnostics (base class).

    Parameters
    ----------
    work_dir:
        Work directory where files created by the diagnostic are stored.

    """

    _VARS: dict[str, dict[str, str]]

    def __init__(
        self,
        work_dir: Path,
        fail_on_missing_variable: bool = True,
    ) -> None:
        """Initialize class instance."""
        self._root_dir = Path(inspect.getfile(self.__class__)).parent
        self._data_dir = self._root_dir / "data"
        self._session_dir = self._get_session_dir(work_dir)
        self._fail_on_missing_variable = fail_on_missing_variable
        logger.debug(f"Initialized diagnostic '{self.name}'")

    def run(self, loader: Loader, **kwargs: Any) -> Path:
        """Run diagnostics.

        Parameters
        ----------
        loader:
            Loader instance of hybrid Earth system model output.
        **kwargs
            Additional keyword arguments for running a diagnostic.

        Returns
        -------
        Path
            Diagnostic output directory.

        """
        logger.debug(f"Running diagnostic '{self.name}'")

        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created session directory {self.session_dir}")
        logger.debug(f"Created input directory {self.input_dir}")
        logger.debug(f"Created output directory {self.output_dir}")

        self._run_diag(loader, **kwargs)

        logger.debug(f"Finished diagnostic '{self.name}'")

        return self.output_dir

    @property
    def input_dir(self) -> Path:
        """Get input directory."""
        return self._session_dir / "input"

    @property
    def output_dir(self) -> Path:
        """Get output directory."""
        return self._session_dir / "output"

    @property
    def name(self) -> str:
        """Get name of diagnostic."""
        return self._root_dir.name

    @property
    def session_dir(self) -> Path:
        """Get output directory."""
        return self._session_dir

    def _get_better_long_name(
        self,
        var_id: str,
        short_name: str,
        long_name: str,
    ) -> str:
        """Get better variable long name that can be used for plots"""
        special_names = {
            "asr": "Absorbed Shortwave Radiation",
            "clt": "Total Cloud Cover",
            "rtmt": "TOA Net Downward Total Radiation",
        }
        better_long_name = special_names.get(short_name, long_name)

        # Handle variable IDs with vertical level information, e.g., ta20000
        if var_id != short_name:
            level = int(int(var_id.replace(short_name, "")) / 100)
            better_long_name += f" at {level} hPa"

        return better_long_name

    def _get_session_dir(self, work_dir: Path) -> Path:
        """Get session directory."""
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        session_dir = work_dir / f"{self.name}_{now}"
        return session_dir

    def _run_diag(self, loader: Loader, **kwargs: Any) -> None:
        """Run diagnostic function.

        Should be implemented by child classes.

        """
        raise NotImplementedError()


class ESMValToolDiagnostic(Diagnostic):
    """Run ESMValTool diagnostics (base class).

    Parameters
    ----------
    work_dir:
        Work directory where files created by the diagnostic are stored.

    """

    _BASE_CFG: dict[str, Any] = {
        "log_level": "info",
        "output_file_type": "png",
        "recipe": "recipe.yml",
    }
    _DIAG_CFG: dict[str, Any]

    def _get_cfg(
        self,
        loader: Loader,
        **additional_cfg: Any,
    ) -> dict[str, Any]:
        """Get configuration dictionary for ESMValTool diagnostic."""
        cfg: dict[str, Any] = {
            **self._BASE_CFG,
            **self._DIAG_CFG,
        }

        # Create input/output directories
        aux_dir = self.input_dir / "aux"
        plot_dir = self.output_dir / "plots"
        run_dir = self.output_dir / "run"
        work_dir = self.output_dir / "work"
        for dir_ in (aux_dir, plot_dir, run_dir, work_dir):
            dir_.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory {dir_}")

        # Setup input data
        metadata_dict: dict[str, dict] = {}
        file_idx = 0

        # Hybrid ESM input data
        logger.debug(
            f"Using variables {list(self._VARS)} for diagnostic '{self.name}'"
        )
        for var_id, var_dict in self._VARS.items():
            try:
                cube = loader.load_variable(**var_dict)
            except Exception as exc:
                msg = (
                    f"Failed to extract variable '{var_id}' from {loader.path}"
                )
                if self._fail_on_missing_variable:
                    raise HybridESMBenchException(msg)
                msg = f"{msg}: {exc}"
                warnings.warn(msg, HybridESMBenchWarning, stacklevel=2)
                continue
            logger.debug(
                f"Running preprocessor on variable '{var_id}' for diagnostic "
                f"'{self.name}'"
            )
            cube = self._preprocess(var_id, cube)
            path = self.input_dir / f"{var_id}_{loader.path.name}.nc"
            logger.debug(f"Saving {path}")
            iris.save(cube, path)
            logger.debug(f"Saved {path}")

            # Setup metadata for hybrid ESM output
            metadata = loader.get_metadata(**var_dict)
            metadata["diagnostic"] = self.name
            metadata["filename"] = str(path)
            metadata["preprocessor"] = f"{self.name}_preprocessor"
            metadata["recipe_dataset_index"] = file_idx
            metadata["variable_group"] = var_id

            # Data-specific metadata
            metadata["long_name"] = cube.long_name
            metadata["short_name"] = cube.var_name
            metadata["standard_name"] = cube.standard_name
            metadata["units"] = str(cube.units)
            timerange = get_timerange(cube)
            if timerange is not None:
                metadata["timerange"] = timerange
                metadata["start_year"] = timerange.split("/")[0][:4]
                metadata["end_year"] = timerange.split("/")[1][:4]

            metadata = self._update_metadata(var_id, metadata)

            metadata_dict[str(path)] = metadata
            file_idx += 1

        # Other input data
        for metadata_file in self._data_dir.rglob("metadata.yml"):
            with metadata_file.open("r", encoding="utf-8") as file:
                metadata = yaml.safe_load(file)
                logger.debug(f"Loaded metadata file {metadata_file}")

            for filename in metadata:
                filepath = str(self._data_dir / filename)
                metadata_dict[filepath] = metadata[filename]
                metadata_dict[filepath]["filename"] = filepath
                metadata_dict[filepath]["recipe_dataset_index"] = file_idx
                file_idx += 1

        new_metadata_file = self.input_dir / "metadata.yml"
        with new_metadata_file.open("w", encoding="utf-8") as file:
            yaml.safe_dump(metadata_dict, file)
            logger.debug(f"Wrote metadata file {new_metadata_file}")

        # Add directories to cfg
        cfg.update(
            {
                "auxiliary_data_dir": str(aux_dir),
                "input_data": metadata_dict,
                "input_files": [str(new_metadata_file)],
                "plot_dir": str(plot_dir),
                "run_dir": str(run_dir),
                "work_dir": str(work_dir),
            },
        )

        # Additional options from child diagnostics
        cfg = self._update_cfg(cfg, loader)

        # Additional options from user
        cfg.update(additional_cfg)

        return cfg

    def _preprocess(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        return cube

    def _run_diag(self, loader: Loader, **kwargs: Any) -> None:
        """Run diagnostic function."""
        logger.debug(f"Creating cfg for ESMValTool diagnostic '{self.name}'")
        cfg = self._get_cfg(loader, **kwargs)
        logger.debug(f"Running ESMValTool diagnostic '{self.name}'")
        self._run_esmvaltool_diag(cfg)

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic.

        Should be implemented by child classes.

        """
        raise NotImplementedError()

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        return cfg

    def _update_metadata(
        self,
        var_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        return metadata
