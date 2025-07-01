"""Create, couple, test, and evaluate hybrid Earth system model simulations."""

import sys

from loguru import logger

logger.remove()
logger.add(sys.stdout, colorize=True)
