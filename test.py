from pathlib import Path
from pprint import pprint

from hybridesmbench.eval._diags.timeseries import TimeSeriesDiagnostic

d = TimeSeriesDiagnostic(Path("/home/manuel/tmp/hybridesmbench"))

d.run(
    Path("/mnt/d/data/icon/ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"),
    "icon",
)

pprint(list(d.get_all_figures()))

pprint(list(d.get_all_nc_files()))
