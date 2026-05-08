"""
Detect protocols that pick up more tips than the loaded tip racks contain.
Severity: high.
"""

from typing import Any
from ..recommendation import Recommendation

_TIPRACK_CAPACITY: list[tuple] = [
    ("96_tiprack", 96),
    ("96_filter",  96),
    ("tiprack_96", 96),
]


def _count_tip_capacity(slot_labware: dict) -> int:
    total = 0
    for lw_name in slot_labware.values():
        lw_lower = lw_name.lower()
        for hint, cap in _TIPRACK_CAPACITY:
            if hint in lw_lower:
                total += cap
                break
    return total


def detect(protocol: Any, snapshots: Any) -> list:
    capacity = _count_tip_capacity(protocol.slot_labware)
    pickups = sum(1 for s in protocol.steps if s.action == "pick_up_tip")

    if capacity == 0 or pickups <= capacity:
        return []

    short_by = pickups - capacity
    return [
        Recommendation(
            issue_type="tip_rack_exhaustion",
            severity="high",
            step_index=-1,
            message=(
                f"Protocol picks up {pickups} tips but only {capacity} are "
                f"loaded across all tip racks (short by {short_by})."
            ),
            suggested_fix=(
                f"Either load {(short_by + 95) // 96} additional 96-tip rack(s) "
                f"on a free deck slot, or reduce tip usage (e.g. reuse tips "
                f"with new_tip='never' where contamination is not a concern)."
            ),
            metadata={"pickups": pickups, "capacity": capacity, "shortfall": short_by},
        )
    ]
