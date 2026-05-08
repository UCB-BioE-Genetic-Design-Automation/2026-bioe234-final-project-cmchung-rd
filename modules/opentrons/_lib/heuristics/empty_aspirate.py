"""
Detect aspirations that pull more liquid than is currently in the well.
Severity: high.
"""

from typing import Any
from ..recommendation import Recommendation

_EPSILON = 0.5


def detect(protocol: Any, snapshots: Any) -> list:
    out: list[Recommendation] = []
    snap_by_idx = {s.step_index: s for s in snapshots}

    for step in protocol.steps:
        if step.action != "aspirate":
            continue

        max_vol = protocol.slot_max_volumes.get(step.slot, 0)
        if max_vol == 0 or max_vol == float("inf"):
            continue

        prior = snap_by_idx.get(step.step_index - 1)
        if prior is None:
            continue

        available = prior.well_volumes.get((step.slot, step.well), 0.0)
        requested = step.volume_ul or 0.0

        if requested > available + _EPSILON:
            out.append(
                Recommendation(
                    issue_type="empty_aspirate",
                    severity="high",
                    step_index=step.step_index,
                    message=(
                        f"Step {step.step_index}: aspirating {requested:.1f} µL from "
                        f"{step.slot}/{step.well}, but only {available:.1f} µL is "
                        f"available."
                    ),
                    suggested_fix=(
                        f"Either declare an initial volume for {step.slot}/{step.well} "
                        f"with a `# INIT slot {step.slot} {step.well} <volume>uL` "
                        f"directive, or reduce the requested aspirate to at most "
                        f"{available:.1f} µL."
                    ),
                    affected_wells=[step.well],
                    metadata={
                        "slot": step.slot,
                        "requested_uL": requested,
                        "available_uL": available,
                    },
                )
            )

    return out
