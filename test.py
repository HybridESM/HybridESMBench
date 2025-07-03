from pathlib import Path

from hybridesmbench.eval._diags.timeseries import TimeSeriesDiagnostic

d = TimeSeriesDiagnostic(Path("/scratch/b/b309141/esmvaltool_output"))

d.run(
    Path(
        "/work/bd1179/b309170/icon-ml_models/icon-a-ml/experiments/"
        "ag_atm_amip_r2b5_auto_tuned_baseline_20yrs/"
    )
)

print(list(d.get_all_figures()))

print(list(d.get_all_nc_files()))
