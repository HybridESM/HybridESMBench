from pathlib import Path
from pprint import pprint

from hybridesmbench.eval._diags.timeseries import TimeSeriesDiagnostic

d = TimeSeriesDiagnostic(Path("/scratch/b/b309141/esmvaltool_output"))

d.run()

pprint(list(d.get_all_figures()))

pprint(list(d.get_all_nc_files()))
