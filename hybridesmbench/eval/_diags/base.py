"""Provide base class for diagnostics."""

import datetime
import inspect
import warnings
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from hybridesmbench.exceptions import HybridESMBenchWarning


class Diagnostic:
    """Setup base class for diagnostics.

    Parameters
    ----------
    output_dir:
        Output directory.
    **additional_settings:
        Additional diagnostic settings.

    """

    _BASE_SETTINGS: dict[str, Any] = {
        "log_level": "info",
        "output_file_type": "png",
        "recipe": "recipe.yml",
    }
    _SETTINGS: dict[str, Any] = {}
    _VARS: list[dict[str, str]] = []

    def __init__(self, work_dir: Path, **additional_settings: Any) -> None:
        """Initialize class instance."""
        logger.info(f"Initializing diagnostic '{self.name}'")
        self._session_dir = self._get_session_dir(work_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created input directory {self.input_dir}")
        logger.debug(f"Created output directory {self.output_dir}")

        self._cfg = self._get_cfg(**additional_settings)

    def get_all_figures(self, suffix: str = "png") -> list[Path]:
        """Get all figure files."""
        return self._get_all_output_files(suffix)

    def get_all_nc_files(self, suffix: str = "nc") -> list[Path]:
        """Get all figure files."""
        return self._get_all_output_files(suffix)

    def run(self) -> None:
        """Run diagnostic."""
        raise NotImplementedError()

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

    @property
    def _data_dir(self) -> Path:
        """Get data directory."""
        return self._root_dir / "data"

    @property
    def _root_dir(self) -> Path:
        """Get root directory of diagnostic."""
        return Path(inspect.getfile(self.__class__)).parent

    def _get_all_output_files(self, suffix: str | None = None) -> list[Path]:
        """Get all output files."""
        files = list(self.output_dir.rglob(f"*.{suffix}"))
        if not files:
            warnings.warn(
                f"No files of type '{suffix}' available, make sure to run() "
                f"the diagnostic first",
                HybridESMBenchWarning,
                stacklevel=3,
            )
        return files

    def _get_cfg(self, **additional_settings: Any) -> dict[str, Any]:
        """Get configuration dictionary for diagnostic."""
        cfg: dict[str, Any] = {
            **self._BASE_SETTINGS,
            **self._SETTINGS,
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
        for metadata_file in self._data_dir.rglob("metadata.yml"):
            with metadata_file.open("r", encoding="utf-8") as file:
                metadata = yaml.safe_load(file)
                logger.debug(f"Loaded metadata file {metadata_file}")

            for file_idx, filename in enumerate(metadata):
                filepath = str(self._data_dir / filename)
                new_metadata[filepath] = metadata[filename]
                new_metadata[filepath]["filename"] = filepath
                new_metadata[filepath]["recipe_dataset_index"] = file_idx

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

        cfg.update(additional_settings)

        return cfg

    def _get_session_dir(self, work_dir: Path) -> Path:
        """Get session directory."""
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        session_dir = work_dir / f"{self.name}_{now}"
        session_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created session directory {session_dir}")
        return session_dir
