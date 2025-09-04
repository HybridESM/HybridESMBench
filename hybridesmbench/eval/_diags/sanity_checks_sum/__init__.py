"""Run sanity checks diagnostic."""

import warnings
from typing import Any

import iris
import yaml
from esmvalcore.preprocessor import (
    anomalies,
    area_statistics,
    convert_units,
    regrid,
)
from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets
from iris import Constraint
from iris.cube import Cube
from loguru import logger

from hybridesmbench._utils import (
    get_timerange,
)
from hybridesmbench.eval._diags import ESMValToolDiagnostic
from hybridesmbench.eval._loaders import Loader
from hybridesmbench.exceptions import (
    HybridESMBenchException,
    HybridESMBenchWarning,
)


class SanityChecksDiagnostic(ESMValToolDiagnostic):
    """Run sanity checks diagnostic."""

    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "timeseries": {
                "pyplot_kwargs": {
                    "title": "{title}",
                },
                "plot_kwargs": {
                    "default": {
                        "color": "red",
                        "label": None,
                        "linewidth": 2.0,
                        "zorder": 1.0,
                    },
                },
            },
        },
    }
    _VARS = {
        "ps": {"var_name": "ps", "mip_table": "Amon"},
        "prw": {"var_name": "prw", "mip_table": "Amon"},
        # "qep": {"var_name": "qep", "mip_table": "Amon"},
    }

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
                # get time range for the plot
                time_coord = cube.coord("time")
                start_date = time_coord.cell(0).point
                end_date = time_coord.cell(-1).point
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
            if var_id == "ps":
                cube = self._preprocess_anom(var_id, cube)
            else:
                cube = self._preprocess_sum(var_id, cube)
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

            metadata = self._update_metadata(var_id, loader, metadata)

            metadata_dict[str(path)] = metadata
            file_idx += 1

        # Other input data
        for metadata_file in self._data_dir.rglob("metadata.yml"):
            with metadata_file.open("r", encoding="utf-8") as file:
                metadata = yaml.safe_load(file)
                logger.debug(f"Loaded metadata file {metadata_file}")
                # update title in metadata
                for mfile in metadata.keys():
                    var = metadata[mfile]["short_name"]
                    metadata[mfile] = self._update_metadata(
                        var, loader, metadata[mfile]
                    )

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
        cfg = self._update_cfg(cfg, loader, start_date, end_date)

        # Additional options from user
        cfg.update(additional_cfg)

        return cfg

    def _preprocess_anom(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "sum")
        cube = anomalies(cube, "full")

        return cube

    def _preprocess_sum(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        if cube.var_name == "ps":
            cube = convert_units(cube, "kg m-2")
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "sum")

        return cube

    def _run_esmvaltool_diag(self, cfg: dict[str, Any]) -> None:
        """Run ESMValTool diagnostic."""
        # TODO: this entire block can be replaced with main(cfg) in
        # ESMValTool v2.13.0
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Using DEFAULT_SPHERICAL_EARTH_RADIUS",
                category=UserWarning,
                module="iris",
            )
            MultiDatasets(cfg).compute()

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
        start_date,
        end_date,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        plot_kwargs = {
            "color": "C0",
            "label": "{alias}",
            "linewidth": 1.25,
            "zorder": 2.5,
        }
        plot_kwargs_ranges = {
            "color": "red",
            "label": None,
            "linewidth": 2.0,
            "zorder": 1.0,
        }
        cfg["plots"]["timeseries"]["plot_kwargs"][
            loader.model_name
        ] = plot_kwargs
        cfg["plots"]["timeseries"]["plot_kwargs"][
            "MultiModelMin"
        ] = plot_kwargs_ranges
        cfg["plots"]["timeseries"]["plot_kwargs"][
            "MultiModelMax"
        ] = plot_kwargs_ranges
        cfg["plots"]["timeseries"]["pyplot_kwargs"]["xlim"] = [
            start_date,
            end_date,
        ]
        return cfg

    def _update_metadata(
        self,
        var_id: str,
        loader: Loader,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update hybrid ESM output metadata (in-place)."""
        better_long_name = self._get_better_long_name(
            var_id, metadata["short_name"], metadata["long_name"]
        )
        if var_id == "ps":
            metadata["title"] = "Anomaly of Global Air Mass"
        else:
            metadata["title"] = f"Global Sum of {better_long_name}"
        return metadata
