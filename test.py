import sys
from pprint import pprint
from typing import Literal

from distributed import Client
from loguru import logger

from hybridesmbench.eval import evaluate


def main():
    """Test HybridESMBench."""
    logger.remove()
    logger.add(sys.stdout, colorize=True)

    cluster_kwargs = dict(
        n_workers=6,
        threads_per_worker=2,
        memory_limit="6 GiB",
    )
    client = Client(**cluster_kwargs)
    print("Dask dashboard:", client.dashboard_link)

    # icon_output = (
    #   "/mnt/d/data/icon/ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"
    # )
    icon_output = (
        "/work/bd1179/b309170/icon-ml_models/icon-a-ml/experiments/"
        "ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"
    )
    model_type: Literal["icon"] = "icon"
    # work_dir = "/home/manuel/tmp/hybridesmbench"
    work_dir = "/scratch/b/b309141/hybridesmbench_output"

    output = evaluate(
        icon_output,
        model_type,
        work_dir,
        model_name="My ICON",
        # diagnostics=["timeseries"],
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
