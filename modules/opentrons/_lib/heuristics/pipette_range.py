"""
Detect aspirate/dispense volumes outside the pipette's working range.
Severity: high.
"""

import re
from typing import Any
from ..recommendation import Recommendation

_TIPRACK_RANGES: list[tuple] = [
    ("10ul",   1.0,    10.0),
    ("20ul",   1.0,    20.0),
    ("50ul",   5.0,    50.0),
    ("200ul",  20.0,  200.0),
    ("300ul",  20.0,  300.0),
    ("1000ul", 100.0, 1000.0),
]


def _infer_pipette_range(slot_labware: dict) -> tuple | None:
    best = None
    for lw_name in slot_labware.values():
        lw_lower = re.sub(r"\s+", "", lw_name.lower())
        for hint, lo, hi in _TIPRACK_RANGES:
            if hint in lw_lower:
                if best is None or hi > best[1]:
                    best = (lo, hi)
    return best


def detect(protocol: Any, snapshots: Any) -> list:
    rng = _infer_pipette_range(protocol.slot_labware)
    if rng is None:
        return []
    lo, hi = rng

    out: list[Recommendation] = []
    for step in protocol.steps:
        if step.action not in ("aspirate", "dispense"):
            continue
        v = step.volume_ul
        if v is None:
            continue
        if v < lo:
            out.append(_make_rec(step, v, lo, hi, "below"))
        elif v > hi:
            out.append(_make_rec(step, v, lo, hi, "above"))

    return out


def _make_rec(step, v: float, lo: float, hi: float, side: str) -> Recommendation:
    direction = "below the minimum" if side == "below" else "above the maximum"
    bound = lo if side == "below" else hi
    return Recommendation(
        issue_type="pipette_range",
        severity="high",
        step_index=step.step_index,
        message=(
            f"Step {step.step_index}: {step.action} of {v:.1f} µL is "
            f"{direction} accurate range ({lo:.1f}–{hi:.1f} µL)."
        ),
        suggested_fix=(
            f"Adjust the volume to within {lo:.1f}–{hi:.1f} µL, or load a "
            f"different pipette/tiprack capable of {v:.1f} µL."
        ),
        metadata={"volume_uL": v, "pipette_min": lo, "pipette_max": hi, "violated_bound": bound},
    )
