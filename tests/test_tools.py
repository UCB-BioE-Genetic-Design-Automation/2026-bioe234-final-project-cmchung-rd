"""
Unit tests for the seq_basics example tools and the opentrons pipeline tools.

Each tool follows the Python Function Object Pattern (initiate / run).
Tests cover the module-level aliases produced by _instance.run.
"""

import json
import pytest

from modules.seq_basics.tools.translate import translate
from modules.seq_basics.tools.reverse_complement import reverse_complement


# ---------------------------------------------------------------------------
# seq_basics tests
# ---------------------------------------------------------------------------

def test_reverse_complement_basic():
    assert reverse_complement("ATGC") == "GCAT"


def test_reverse_complement_ambiguity_codes():
    assert reverse_complement("ATRYSWKMN")


def test_translate_basic():
    assert translate("ATGGCT") == "MA"


def test_translate_frame_validation():
    with pytest.raises(ValueError):
        translate("ATGGCT", frame=0)
    with pytest.raises(ValueError):
        translate("ATGGCT", frame=4)


def test_translate_with_coordinates_and_frame():
    assert translate("AATGGCTAAA", start=1, end=None, frame=1) == "MAK"


# ---------------------------------------------------------------------------
# opentrons / generate_protocol tests (no OT venv required)
# ---------------------------------------------------------------------------

from modules.opentrons.tools.generate_protocol import generate_protocol


def test_generate_serial_dilution_returns_script():
    params = json.dumps({"num_dilutions": 8, "dilution_factor": 2, "initial_volume": 100})
    raw = generate_protocol("serial_dilution", params)
    result = json.loads(raw)
    assert "script" in result, result
    assert "protocol_api" in result["script"]


def test_generate_pcr_setup_returns_script():
    params = json.dumps({"num_samples": 24, "master_mix_volume": 25, "sample_volume": 5, "total_volume": 50})
    raw = generate_protocol("pcr_setup", params)
    result = json.loads(raw)
    assert "script" in result, result


def test_generate_unknown_task_returns_error():
    raw = generate_protocol("unknown_task", "{}")
    result = json.loads(raw)
    assert "error" in result


def test_generate_bad_json_returns_error():
    raw = generate_protocol("serial_dilution", "not valid json {{")
    result = json.loads(raw)
    assert "error" in result


# ---------------------------------------------------------------------------
# opentrons / analyze_protocol tests (no OT venv required)
# ---------------------------------------------------------------------------

from modules.opentrons.tools.analyze_protocol import analyze_protocol

_MINIMAL_LOG = """\
Picking up tip from A1 of Opentrons 96 Tip Rack 300 µL on 1
Aspirating 200 uL from A1 of Corning 96 Well Plate 360 µL Flat on 2 at 1.0 speed
Dispensing 200 uL into B1 of Corning 96 Well Plate 360 µL Flat on 2 at 1.0 speed
Dropping tip into A1 of Opentrons Fixed Trash on 12
"""


def test_analyze_returns_recommendations_key():
    raw = analyze_protocol(_MINIMAL_LOG)
    result = json.loads(raw)
    assert "recommendations" in result, result


def test_analyze_empty_log_does_not_crash():
    raw = analyze_protocol("")
    result = json.loads(raw)
    assert isinstance(result, dict)
