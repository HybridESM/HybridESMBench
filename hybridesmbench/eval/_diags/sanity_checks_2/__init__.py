"""Run santiy checks diagnostic."""

import warnings
from typing import Any

from esmvalcore.preprocessor import (
    area_statistics,
    anomalies,
    climate_statistics,
    convert_units,
    regrid,
)
from esmvaltool.diag_scripts.monitor.multi_datasets import MultiDatasets
import copy
import iris
import yaml
from iris import Constraint
from iris.cube import Cube
from loguru import logger

from hybridesmbench._utils import (
    extract_final_20_years,
    extract_vertical_level,
    get_timerange,
)
from hybridesmbench.eval._diags import ESMValToolDiagnostic
from hybridesmbench.eval._loaders import Loader


class SanityChecksDiagnostic(ESMValToolDiagnostic):
    """Run sanity checks diagnostic."""

    # _OBS_PLOT_KWARGS = {
    #     "color": "black",
    #     "label": "{dataset}",
    #     "linewidth": 1.0,
    #     "zorder": 2.4,
    # }
    _DIAG_CFG = {
        "facet_used_for_labels": "alias",
        "group_variables_by": "variable_group",
        "plot_filename": "{plot_type}_{exp}_{real_name}_{dataset}_{mip}",
        "plot_folder": "{plot_dir}",
        "plots": {
            "timeseries": {
                # "legend_kwargs": {
                #     "loc": "upper center",
                #     "bbox_to_anchor": [0.5, -0.2],
                #     "borderaxespad": 0.0,
                # },
                "pyplot_kwargs": {
                    "title": "{title}",
                }, 
                "plot_kwargs": {
                    "default": {
                        "color": "lightgray",
                        "label": None,
                        "linewidth": 0.75,
                        "zorder": 1.0,
                    },
                },
                "hlines": [
                    {"y": 0.46, "color": "red", "linewidth": 2},
                    {"y": 0., "color": "red", "linewidth": 2},
                ],
            },
        },
    }
    _VARS = {
        # "asr": {"var_name": "asr", "mip_table": "Amon"},
        "clivi": {"var_name": "clivi", "mip_table": "Amon"},
        # "clt": {"var_name": "clt", "mip_table": "Amon"},
        # "hfls": {"var_name": "hfls", "mip_table": "Amon"},
        # "hfss": {"var_name": "hfss", "mip_table": "Amon"},
        # # "lwcre": {"var_name": "lwcre", "mip_table": "Amon"},
        # # "lwp": {"var_name": "lwp", "mip_table": "Amon"},
        # # "netcre": {"var_name": "netcre", "mip_table": "Amon"},
        # "pr": {"var_name": "pr", "mip_table": "Amon"},
        # "prc": {"var_name": "pr", "mip_table": "Amon"},
        # "prw": {"var_name": "prw", "mip_table": "Amon"},
        # "rlds": {"var_name": "rlds", "mip_table": "Amon"},
        # "rlut": {"var_name": "rlut", "mip_table": "Amon"},
        # "rsds": {"var_name": "rlds", "mip_table": "Amon"},
        # "rsut": {"var_name": "rsut", "mip_table": "Amon"},
        # # "rtnt": {"var_name": "rtnt", "mip_table": "Amon"},
        # # "swcre": {"var_name": "swcre", "mip_table": "Amon"},
        # "tas": {"var_name": "tas", "mip_table": "Amon"},
        # "tauu": {"var_name": "tauu", "mip_table": "Amon"},
        # "tauv": {"var_name": "tauu", "mip_table": "Amon"},
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
            cube_min = copy.deepcopy(cube)
            cube_max = copy.deepcopy(cube)
            cube = self._preprocess(var_id, cube)
            cube_min = self._preprocess_min(var_id, cube_min)
            cube_max = self._preprocess_max(var_id, cube_max)
            path = self.input_dir / f"{var_id}_{loader.path.name}.nc"
            path_min = self.input_dir / f"{var_id}_{loader.path.name}_min.nc"
            path_max = self.input_dir / f"{var_id}_{loader.path.name}_max.nc"
            logger.debug(f"Saving {path}")
            iris.save(cube, path)
            iris.save(cube_min, path_min)
            iris.save(cube_max, path_max)
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

            # Adding metadata for min and max
            metadata_min = copy.deepcopy(metadata)
            metadata_min["alias"] = "global_min"
            metadata_min["filename"] = str(path_min)
            metadata_min["recipe_dataset_index"] = file_idx
            metadata_dict[str(path_min)] = metadata_min
            file_idx += 1
            metadata_max = copy.deepcopy(metadata)
            metadata_max["alias"] = "global_max"
            metadata_max["filename"] = str(path_max)
            metadata_max["recipe_dataset_index"] = file_idx
            metadata_dict[str(path_max)] = metadata_max
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
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "mean")
        if cube.var_name == "pr":
            cube = convert_units(cube, "mm day-1")
        
        return cube
    
    def _preprocess_min(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "min")
        if cube.var_name == "pr":
            cube = convert_units(cube, "mm day-1")
        
        return cube
    
    def _preprocess_max(self, var_id: str, cube: Cube) -> Cube:
        """Preprocess input data."""
        cube = cube.extract(Constraint(time=lambda c: c.point.year >= 1979))
        cube = regrid(cube, "2x2", "area_weighted", cache_weights=True)
        cube = area_statistics(cube, "max")
        if cube.var_name == "pr":
            cube = convert_units(cube, "mm day-1")
        
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
            print(cfg)
            MultiDatasets(cfg).compute()

    def _update_cfg(
        self,
        cfg: dict[str, Any],
        loader: Loader,
    ) -> dict[str, Any]:
        """Update diagnostic configuration settings (in-place)."""
        plot_kwargs = {
            "color": "C0",
            "label": "{alias}",
            "linewidth": 1.25,
            "zorder": 2.5,
        }
        plot_kwargs_minmax = {
            "color": "C0",
            #"label": "{alias}",
            "label": None,
            "linewidth": 1.25,
            "zorder": 2.3,
            "linestyle": "--",
        }
        cfg["plots"]["timeseries"]["plot_kwargs"][
            loader.model_name
        ] = plot_kwargs
        cfg["plots"]["timeseries"]["plot_kwargs"][
            "global_min"
        ] = plot_kwargs_minmax
        cfg["plots"]["timeseries"]["plot_kwargs"][
            "global_max"
        ] = plot_kwargs_minmax
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
        metadata["title"] = f"Global Mean of {better_long_name}"
        return metadata