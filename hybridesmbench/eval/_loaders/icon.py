"""Load ICON hybrid Earth system model output."""

from hybridesmbench.eval._loaders import BaseICONLoader


class ICONLoader(BaseICONLoader):
    """Load ICON hybrid Earth system model output.

    Parameters
    ----------
    path:
        Path to ICON output.

    """

    _DATASET = "ICON"
    _VAR_TYPES = {
        "pr": "atm_2d_ml",
        "rlut": "atm_2d_ml",
        "rsut": "atm_2d_ml",
        "rtmt": "atm_2d_ml",
        "tas": "atm_2d_ml",
    }
