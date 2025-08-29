import logging
import sys
import warnings
from pprint import pprint

from distributed import Client
from loguru import logger

from hybridesmbench.eval import evaluate
from hybridesmbench.typing import ModelType


def main():
    """Test HybridESMBench."""
    # Setup logging
    logger.remove()
    logger.add(sys.stdout, colorize=True)
    logging.getLogger("esmvalcore").setLevel(logging.ERROR)

    cluster_kwargs = dict(
        n_workers=6,
        threads_per_worker=2,
        memory_limit="6 GiB",
    )
    client = Client(**cluster_kwargs)
    print("Dask dashboard:", client.dashboard_link)

    # modeL_output = (
    #   "/mnt/d/data/icon/ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"
    # )
    model_output = (
        # "/work/bd1179/b309170/icon-ml_models/icon-a-ml/experiments/"
        # "ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"
        "/work/bd1179/b309275/icon-ml_models/icon-a-ml_for_Arthur/"
        "experiments/ag_atm_amip_r2b5_cov15_tuned_Arthur_long/"
    )
    model_output = (
        "/work/bd0854/b309137/HybridESMBench/github/data/arpgem/v20250822/arpgem_NNv2/"
    )
    # model_output = (
    #     "/work/bd0854/DATA/ESMValTool2/CMIP6_DKRZ/CMIP/MPI-M/MPI-ESM1-2-LR/"
    #     "historical/r1i1p1f1/Amon"
    # )

    #model_type: ModelType = "icon"
    model_type: ModelType = "cmip"

    # work_dir = "/home/manuel/tmp/hybridesmbench"
    work_dir = "/scratch/b/b309059/hybridesmbench_output"

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        output = evaluate(
            model_output,
            model_type,
            work_dir,
            model_name="ARPGEM_NNv2",
            diagnostics=["sanity_checks_1", "sanity_checks_2"],
            # diagnostics=["maps", "profiles"],
            # fail_on_diag_error=False,
            fail_on_missing_variable=False,
        )

    for diag_name, diag_output in output.items():
        print(diag_name)
        if diag_output is None:
            print("No output")
            print()
            continue
        pprint(list(diag_output.rglob("*.png")))
        print()


if __name__ == "__main__":
    main()
