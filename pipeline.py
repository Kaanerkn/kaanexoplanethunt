import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# Helpers
# -----------------------------

def to_float(x):
    """Convert value to float, return NaN on failure."""
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return np.nan

# Column name candidates for different catalog formats
CANDIDATE = {
    "id":      ["toi", "tic", "pl_name", "id", "object", "name", "candidate"],
    "orbper":  ["orbper", "period", "pl_orbper", "orbital_period", "per"],
    "trandur": ["trandur", "pl_trandur", "pl_trandurh", "duration", "transit_duration", "t_dur", "tdur"],
    "trandept":["trandept", "pl_trandep", "depth", "transit_depth", "ppm", "deph", "tr_depth", "depth_ppm"],
    "tmag":    ["tmag", "st_tmag", "tic_tmag", "mag", "t_mag", "stellar_tmag"],
}

def _pick(df: pd.DataFrame, keys):
    """Find a suitable column in df that matches any of the given keys."""
    lm = {c.lower(): c for c in df.columns}
    # exact match
    for k in keys:
        if k.lower() in lm:
            return lm[k.lower()]
    # partial match
    for k in keys:
        for lc, orig in lm.items():
            if k.lower() in lc:
                return orig
    return None

def read_table(p: Path) -> pd.DataFrame:
    """Read CSV or Excel table with reasonable defaults."""
    if p.suffix.lower() == ".xlsx":
        return pd.read_excel(p)
    return pd.read_csv(p, sep=None, engine="python", comment="#", encoding="utf-8")

def find_cols(df: pd.DataFrame, manual=None, interactive: bool = False):
    """
    Try to detect which columns correspond to orbper, duration, depth, tmag, id.
    interactive=False => as API/pipeline we do NOT ask for input, only auto-detect.
    """
    manual = manual or {}
    m = {}
    for role, keys in CANDIDATE.items():
        if role in manual and manual[role] in df.columns:
            m[role] = manual[role]
        else:
            m[role] = _pick(df, keys)

    needed = ["orbper", "trandur", "trandept", "tmag"]
    missing = [r for r in needed if (m.get(r) is None or m[r] not in df.columns)]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))
    return m

# -----------------------------
# Scoring functions
# -----------------------------

def f_tmag(x):     return 1.0 if x < 12 else 0.5
def f_depth(x):    return 1.0 if x > 500 else 0.3
def f_period(x):   return 1.0 if x < 30 else 0.4
def f_duration(x): return 1.0 if x < 10 else 0.6

def score(period, duration, depth, tmag):
    """
    Weighted heuristic score in [0, 100].
    Same logic as your original notebook script.
    """
    w = (0.58, 0.27, 0.08, 0.07)
    s = (
        w[0] * f_tmag(tmag) +
        w[1] * f_depth(depth) +
        w[2] * f_period(period) +
        w[3] * f_duration(duration)
    )
    return 100.0 * s

def label(s, mid: float = 46.0, high: float = 80.0) -> str:
    """Map score to class: CP / PC / APC (confirmed / candidate / ambiguous)."""
    if s >= high:
        return "CP"
    if s >= mid:
        return "PC"
    return "APC"

# -----------------------------
# MAIN PIPELINE FUNCTION
# -----------------------------

def run_pipeline(file_path: str) -> pd.DataFrame:
    """
    Main exoplanet candidate filtering pipeline.

    Parameters
    ----------
    file_path : str
        Input CSV/Excel path (TESS / NASA catalog).

    Returns
    -------
    pd.DataFrame
        Original table + computed 'score' and 'class' columns.
    """
    p = Path(file_path)
    if not p.exists():
        # Kullanıcı tam path vermediyse current working directory üzerinden de dene
        p = Path.cwd() / file_path
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    df = read_table(p)
    cols = find_cols(df, interactive=False)

    scores = []
    labels = []

    for _, row in df.iterrows():
        s = score(
            to_float(row[cols["orbper"]]),
            to_float(row[cols["trandur"]]),
            to_float(row[cols["trandept"]]),
            to_float(row[cols["tmag"]]),
        )
        scores.append(round(s, 1))
        labels.append(label(s))

    out = df.copy()
    out["score"] = scores
    out["class"] = labels   # API'de summary hesaplamak için 'class' adıyla kullanacağız

    return out

  
