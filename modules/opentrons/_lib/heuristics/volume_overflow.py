"""
Detect wells whose tracked volume exceeds the labware's per-well capacity.
Severity: high.
"""

from typing import Any
from ..recommendation import Recommendation

_EPSILON = 0.5


def detect(protocol: Any, snapshots: Any) -> list:
    max_vols = protocol.slot_max_volumes
    seen: set[tuple] = set()
    out: list[Recommendation] = []

    for snap in snapshots:
        for (slot, well), vol in snap.well_volumes.items():
            if (slot, well) in seen:
                continue
            cap = max_vols.get(slot, float("inf"))
            if cap == 0 or cap == float("inf"):
                continue
            if vol > cap + _EPSILON:
                seen.add((slot, well))
                out.append(
                    Recommendation(
                        issue_type="volume_overflow",
                        severity="high",
                        step_index=snap.step_index,
                        message=(
                            f"Well {slot}/{well} reaches {vol:.1f} µL, "
                            f"exceeding the labware capacity of {cap:.1f} µL."
                        ),
                        suggested_fix=(
                            f"Reduce the volume dispensed into {slot}/{well} so the "
                            f"running total stays at or below {cap:.1f} µL. Consider "
                            f"splitting the transfer across multiple wells or "
                            f"using a higher-capacity labware."
                        ),
                        affected_wells=[well],
                        metadata={"slot": slot, "max_volume": cap, "actual_volume": vol},
                    )
                )

    return out
