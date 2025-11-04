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
        "clivi": {"raw_name": "TGCLDIWP"},
        "clwvi": {"raw_name": "TGCLDCWP"},
        "clt": {"raw_name": "CLOUD"},
        # "hus": "Q400",
        "lwp": {"raw_name": "TGCLDLWP"},
        "pr": {"raw_name": "PRECT"},
        "ps": {"raw_name": "PS"},
        "prw": {"raw_name": "TMQ"},
        # "ta": "T200", "T850"
        "tas": {"raw_name": "TREFHT"},
        "tauu": {"raw_name": "TAUX"},
        # "ua": "U200", "U850"
    }