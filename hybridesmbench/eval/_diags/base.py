"""Run diagnostics (base class)."""

import datetime
import inspect
import warnings
from collections.abc import Generator
from pathlib import Path
from typing import Any, Literal

import iris
import yaml
from iris.cube import Cube
from loguru import logger

from hybridesmbench._utils import get_timerange
from hybridesmbench.eval._loaders import LOADERS
from hybridesmbench.eval._loaders.base import Loader
from hybridesmbench.exceptions import HybridESMBenchWarning


class Diagnostic:
    """Run diagnostics (base class).

    Parameters
    ----------
    work_dir:
        Work directory where files created by the diagnostic are stored.

    """

    _VARS: list[dict[str, str]]

    def __init__(self, work_dir: Path) -> None:
        """Initialize class instance."""
        self._root_dir = Path(inspect.getfile(self.__class__)).parent
        self._data_dir = self._root_dir / "data"
        self._session_dir = self._get_session_dir(work_dir)
        logger.debug(f"Initialized diagnostic '{self.diag_name}'")

    def get_all_figures(self, suffix: str = "png") -> Generator[Path]:
        """Get all figure files.

        Parameters
        ----------
        suffix:
            File suffix (extension).

        Yields
        ------
        Generator[Path]
            All figure files.

        """
        return self._get_all_output_files(suffix)

    def get_all_nc_files(self, suffix: str = "nc") -> Generator[Path]:
        """Get all netCDF files.

        Parameters
        ----------
        suffix:
            File suffix (extension).

        Yields
        ------
        Generator[Path]
            All netCDF files.

        """
        return self._get_all_output_files(suffix)

    def run(
        self,
        path: Path,
        model_type: Literal["icon"],
        **kwargs: Any,
    ) -> None:
        """Run diagnostics.

        Parameters
        ----------
        path:
            Path to hybrid Earth system model output.
        model_type:
            Hybrid Earth system model type.
        **kwargs
            Additional keyword arguments for running a diagnostic.

        """
        logger.info(f"Running diagnostic '{self.diag_name}'")

        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created session directory {self.session_dir}")
        logger.debug(f"Created input directory {self.input_dir}")
        logger.debug(f"Created output directory {self.output_dir}")

        assert model_type in LOADERS, f"Invalid model type: '{model_type}'"
        loader = LOADERS[model_type](path)

        self._run_diag(loader, **kwargs)

        logger.info(f"Finished diagnostic '{self.diag_name}'")

    @property
    def input_dir(self) -> Path:
        """Get input directory."""
        return self._session_dir / "input"

    @property
    def output_dir(self) -> Path:
        """Get output directory."""
        return self._session_dir / "output"

    @property
    def diag_name(self) -> str:
        """Get name of diagnostic."""
        return self._root_dir.name

    @property
    def session_dir(self) -> Path:
        """Get output directory."""
        return self._session_dir

    def _get_all_output_files(
        self,
        suffix: str | None = None,
    ) -> Generator[Path]:
        """Get all output files."""
        if not self.output_dir.is_dir():
            msg = (
                "Output directory does not exist, make sure to run() the "
                "diagnostic first"
            )
            warnings.warn(msg, HybridESMBenchWarning, stacklevel=3)
        return self.output_dir.rglob(f"*.{suffix}")

    def _get_session_dir(self, work_dir: Path) -> Path:
        """Get session directory."""
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        session_dir = work_dir / f"{self.diag_name}_{now}"
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
        self, loader: Loader, **additional_cfg: Any
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
        new_metadata: dict[str, dict] = {}
        file_idx = 0

        # Hybrid ESM input data
        for var in self._VARS:
            cube = loader.load_variable(**var)
            logger.debug("Running preprocessor")
            cube = self._preprocess(cube)
            filename = f"{'_'.join(var.values())}_{loader.path.name}.nc"
            path = (
                self.input_dir
                / f"{'_'.join(var.values())}_{loader.path.name}.nc"
            )
            iris.save(cube, path)
            logger.debug(f"Saved {path}")

            # Setup metadata for hybrid ESM output
            metadata = loader.get_metadata(**var)
            metadata["diagnostic"] = self.diag_name
            metadata["filename"] = str(path)
            metadata["preprocessor"] = f"{self.diag_name}_preprocessor"
            metadata["recipe_dataset_index"] = file_idx

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

            metadata = self._update_metadata(metadata)

            new_metadata[str(path)] = metadata
            file_idx += 1

        # Other input data
        for metadata_file in self._data_dir.rglob("metadata.yml"):
            with metadata_file.open("r", encoding="utf-8") as file:
                metadata = yaml.safe_load(file)
                logger.debug(f"Loaded metadata file {metadata_file}")

            for filename in metadata:
                filepath = str(self._data_dir / filename)
                new_metadata[filepath] = metadata[filename]
                new_metadata[filepath]["filename"] = filepath
                new_metadata[filepath]["recipe_dataset_index"] = file_idx
                file_idx += 1

        new_metadata_file = self.input_dir / "metadata.yml"
        with new_metadata_file.open("w", encoding="utf-8") as file:
            yaml.safe_dump(new_metadata, file)
            logger.debug(f"Wrote metadata file {new_metadata_file}")

        # Add directories to cfg
        cfg.update(
            {
                "auxiliary_data_dir": str(aux_dir),
                "input_data": new_metadata,
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

    def _preprocess(self, cube: Cube) -> Cube:
        """Preprocess input data."""
        return cube

    def _run_diag(self, loader: Loader, **kwargs: Any) -> None:
        """Run diagnostic function."""
        cfg = self._get_cfg(loader, **kwargs)
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

    def _update_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Update variable metadata (in-place)."""
        return metadata
