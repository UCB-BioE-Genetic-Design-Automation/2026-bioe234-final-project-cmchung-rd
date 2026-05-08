"""
Detect chains of single aspirate-dispense pairs that could use distribute().
Severity: low.
"""

import re
from typing import Any
from ..recommendation import Recommendation

_TIPRACK_MAX_UL: list[tuple] = [
    ("10ul",     10.0),
    ("20ul",     20.0),
    ("50ul",     50.0),
    ("200ul",   200.0),
    ("300ul",   300.0),
    ("1000ul", 1000.0),
]
_MIN_CHAIN = 3


def _pipette_max(slot_labware: dict) -> float:
    best = 0.0
    for lw_name in slot_labware.values():
        lw = re.sub(r"\s+", "", lw_name.lower())
        for hint, hi in _TIPRACK_MAX_UL:
            if hint in lw:
                best = max(best, hi)
    return best or float("inf")


def detect(protocol: Any, snapshots: Any) -> list:
    pipette_max = _pipette_max(protocol.slot_labware)
    out: list[Recommendation] = []

    steps = protocol.steps
    i = 0
    while i < len(steps) - 1:
        a, d = steps[i], steps[i + 1]
        if not (a.action == "aspirate" and d.action == "dispense"):
            i += 1
            continue

        chain_source = (a.slot, a.well)
        dests: list[str] = [f"{d.slot}/{d.well}"]
        chain_volumes: list[float] = [a.volume_ul or 0.0]
        chain_start = a.step_index
        chain_end = d.step_index

        j = i + 2
        while j < len(steps) - 1:
            a2, d2 = steps[j], steps[j + 1]
            if not (a2.action == "aspirate" and d2.action == "dispense"):
                break
            if (a2.slot, a2.well) != chain_source:
                break
            dests.append(f"{d2.slot}/{d2.well}")
            chain_volumes.append(a2.volume_ul or 0.0)
            chain_end = d2.step_index
            j += 2

        chain_len = len(dests)
        if chain_len >= _MIN_CHAIN:
            total = sum(chain_volumes)
            if total <= pipette_max:
                out.append(
                    Recommendation(
                        issue_type="batchable_transfers",
                        severity="low",
                        step_index=chain_start,
                        step_range=(chain_start, chain_end),
                        message=(
                            f"{chain_len} aspirations from "
                            f"{chain_source[0]}/{chain_source[1]} could be combined "
                            f"into one {total:.1f} µL aspirate + {chain_len} dispenses."
                        ),
                        suggested_fix=(
                            f"Replace the {chain_len} separate transfer() calls with "
                            f"a single distribute() (or one aspirate + N dispenses) "
                            f"from {chain_source[0]}/{chain_source[1]} to "
                            f"{dests}. Saves {chain_len - 1} aspirate cycles."
                        ),
                        affected_wells=[chain_source[1]] + [d.split("/")[1] for d in dests],
                        metadata={
                            "chain_length": chain_len,
                            "total_volume_uL": total,
                            "destinations": dests,
                        },
                    )
                )

        i = j if chain_len >= _MIN_CHAIN else i + 1

    return out
