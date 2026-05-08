"""
Detect tips dropped between consecutive aspirations from the same source.
Severity: medium.
"""

from typing import Any
from ..recommendation import Recommendation


def detect(protocol: Any, snapshots: Any) -> list:
    steps = protocol.steps
    waste_runs: list[dict] = []
    current_run: dict | None = None
    last_aspirate: tuple | None = None

    for step in steps:
        if step.action == "aspirate":
            source = (step.slot, step.well)

            if last_aspirate == source and current_run is not None:
                current_run["drops"] += 1
                current_run["end_step"] = step.step_index

            elif last_aspirate == source:
                current_run = {
                    "start_step": step.step_index,
                    "end_step": step.step_index,
                    "source_slot": step.slot,
                    "source_well": step.well,
                    "drops": 1,
                }
                waste_runs.append(current_run)

            else:
                current_run = None

            last_aspirate = source

        elif step.action == "drop_tip":
            pass

    return [_run_to_recommendation(r) for r in waste_runs if r["drops"] >= 2]


def _run_to_recommendation(run: dict) -> Recommendation:
    drops = run["drops"]
    return Recommendation(
        issue_type="tip_waste",
        severity="med",
        step_index=run["start_step"],
        step_range=(run["start_step"], run["end_step"]),
        message=(
            f"{drops} tip changes between aspirations from the same source "
            f"({run['source_slot']}/{run['source_well']})."
        ),
        suggested_fix=(
            f"Replace the per-iteration pick_up_tip / drop_tip pair with a "
            f"single pick_up_tip before the loop and a single drop_tip after. "
            f"Use new_tip='never' on the transfer call. Saves ~{drops} tips."
        ),
        metadata={"tips_saved": drops},
    )
