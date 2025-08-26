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
        "asr": "atm_2d_ml",
        "clivi": "atm_2d_ml",
        "clwvi": "atm_2d_ml",
        "clt": "atm_2d_ml",
        "hus": "atm_3d_ml",
        "lwcre": "atm_2d_ml",
        "lwp": "atm_2d_ml",
        "pr": "atm_2d_ml",
        "ps": "atm_2d_ml",
        "prw": "atm_2d_ml",
        "rlut": "atm_2d_ml",
        "rsut": "atm_2d_ml",
        "rtmt": "atm_2d_ml",
        "swcre": "atm_2d_ml",
        "ta": "atm_3d_ml",
        "tas": "atm_2d_ml",
        "tauu": "atm_2d_ml",
        "ua": "atm_3d_ml",
    }
