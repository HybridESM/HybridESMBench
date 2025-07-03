import sys
from pprint import pprint

from loguru import logger

from hybridesmbench.eval import evaluate

logger.remove()
logger.add(sys.stdout, colorize=True)

output = evaluate(
    "/mnt/d/data/icon/ag_atm_amip_r2b5_auto_tuned_baseline_20yrs",
    "icon",
    "/home/manuel/tmp/hybridesmbench",
)

pprint(output)
