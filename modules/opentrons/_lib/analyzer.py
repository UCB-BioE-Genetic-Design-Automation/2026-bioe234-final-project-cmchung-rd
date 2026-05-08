"""
Optimization & error-checking orchestrator (Alex Haynes).

Runs all heuristic detectors against simulation logs and returns a
structured dict of recommendations for the LLM.
"""

import json
from typing import Any

from .visualizer.log_parser import parse_log
from .visualizer.state_tracker import build_snapshots
from .recommendation import Recommendation, summarize
from .heuristics import (
    tip_waste,
    volume_overflow,
    empty_aspirate,
    pipette_range,
    batchable_transfers,
    tip_rack_exhaustion,
)


_DETECTORS = (
    tip_waste,
    volume_overflow,
    empty_aspirate,
    pipette_range,
    batchable_transfers,
    tip_rack_exhaustion,
)


def analyze_optimization(simulation_logs: str) -> dict:
    """
    Run all heuristics against simulation logs.

    Returns
    -------
    dict with keys:
        status              : "success" | "error"
        protocol_name       : str
        step_count          : int
        recommendations     : list[dict]  (sorted high → low severity)
        summary             : str   (one-line severity summary)
        error_detail        : str   (empty on success)
    """
    if not simulation_logs or not isinstance(simulation_logs, str):
        return _error("simulation_logs must be a non-empty string.")

    try:
        protocol = parse_log(simulation_logs)
        snapshots = build_snapshots(protocol)
    except Exception as exc:
        return _error(f"Failed to parse logs: {type(exc).__name__}: {exc}")

    all_recs: list[Recommendation] = []
    for detector in _DETECTORS:
        try:
            all_recs.extend(detector.detect(protocol, snapshots))
        except Exception as exc:
            all_recs.append(
                Recommendation(
                    issue_type="heuristic_error",
                    severity="low",
                    step_index=-1,
                    message=(
                        f"Internal: heuristic {detector.__name__} raised "
                        f"{type(exc).__name__}: {exc}"
                    ),
                    suggested_fix="No protocol change required; fix the analyzer.",
                )
            )

    severity_rank = {"high": 0, "med": 1, "low": 2}
    all_recs.sort(key=lambda r: (severity_rank.get(r.severity, 3), r.step_index))

    return {
        "status": "success",
        "protocol_name": protocol.protocol_name,
        "step_count": len(protocol.steps),
        "recommendations": [r.to_dict() for r in all_recs],
        "summary": summarize(all_recs),
        "error_detail": "",
    }


def _error(detail: str) -> dict:
    return {
        "status": "error",
        "protocol_name": "",
        "step_count": 0,
        "recommendations": [],
        "summary": "",
        "error_detail": detail,
    }
