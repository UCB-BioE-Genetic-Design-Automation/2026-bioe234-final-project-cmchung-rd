"""
tools/analyze_protocol.py
==========================
Run heuristic analysis on OT-2 simulation logs and return optimization recommendations.
"""

import json
import matplotlib
matplotlib.use("Agg")

from .._lib.analyzer import analyze_optimization


class AnalyzeProtocol:
    def initiate(self) -> None:
        pass

    def run(self, simulation_log: str) -> str:
        try:
            result = analyze_optimization(simulation_log)
        except Exception as exc:  # noqa: BLE001
            return json.dumps({"error": f"Analysis failed: {exc}"})

        return json.dumps(result)


_instance = AnalyzeProtocol()
_instance.initiate()
analyze_protocol = _instance.run
