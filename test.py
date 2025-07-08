import sys
from pprint import pprint
from typing import Literal

from loguru import logger

from hybridesmbench.eval import evaluate

logger.remove()
logger.add(sys.stdout, colorize=True)


icon_output = "/mnt/d/data/icon/ag_atm_amip_r2b5_auto_tuned_baseline_20yrs"
model_type: Literal["icon"] = "icon"
work_dir = "/home/manuel/tmp/hybridesmbench"

output = evaluate(
    icon_output,
    model_type,
    work_dir,
    diagnostics=["portrait_plot"],
)

pprint(output)
