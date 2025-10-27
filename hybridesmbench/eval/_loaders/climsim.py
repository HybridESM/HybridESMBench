"""Load ClimSim hybrid Earth system model output."""

from hybridesmbench.eval._loaders import BaseClimSimLoader


class ClimSimLoader(BaseClimSimLoader):
    """Load ClimSim hybrid Earth system model output.

    Parameters
    ----------
    path:
        Path to ClimSim output.

    """

    _DATASET = "ClimSim"
    _VAR_NAMES = {
        "clivi": "TGCLDIWP",
        "clwvi": "TGCLDCWP",
        "clt": "CLOUD",
        # "hus": "Q400",
        "lwp": "TGCLDLWP",
        "pr": "PRECT",
        "ps": "PS",
        "prw": "TMQ",
        # "ta": "T200", "T850"
        "tas": "TREFHT",
        "tauu": "TAUX",
        # "ua": "U200", "U850"
    }