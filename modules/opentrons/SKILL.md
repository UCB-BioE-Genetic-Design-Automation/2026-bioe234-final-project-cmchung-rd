# Opentrons OT-2 Protocol Tools

This module provides four tools for generating, simulating, analyzing, and visualizing Opentrons OT-2 liquid-handling protocols, plus a pipeline tool that chains all four.

---

## Tool overview

| Tool | What it does |
|------|-------------|
| `generate_protocol` | LLM-driven script generation from task type + parameters |
| `simulate_protocol` | Dry-run via `opentrons_simulate`; returns full log text |
| `analyze_protocol` | Heuristic analysis → optimization recommendations |
| `visualize_deck_state` | Parse log → PDF report, HTML dashboard, GIF, stats PNG |
| `run_full_pipeline` | Chains all four in sequence; preferred entry point |

---

## Preferred usage

For most user requests, call **`run_full_pipeline`** with `task_type` and `parameters_json`. It handles generate → simulate → analyze → visualize automatically and returns a combined summary with all output file paths.

Only call individual tools when:
- The user already has a simulation log and just wants analysis or visualizations.
- A specific stage failed and needs to be retried in isolation.

---

## task_type values and parameter schemas

### `serial_dilution`

Performs a multi-step serial dilution across columns of a 96-well plate.

```json
{
  "num_dilutions":   8,
  "dilution_factor": 2,
  "initial_volume":  100,
  "diluent_volume":  100
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `num_dilutions` | int | 8 | Number of dilution steps (1–11) |
| `dilution_factor` | number | 2 | Fold-dilution per step |
| `initial_volume` | number | 100 | µL added to first well from stock |
| `diluent_volume` | number | 100 | µL diluent pre-filled in destination wells |

---

### `pcr_setup`

Dispenses master mix and samples into a 96-well PCR plate.

```json
{
  "num_samples":        48,
  "master_mix_volume":  25,
  "sample_volume":       5,
  "total_volume":       50
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `num_samples` | int | 48 | 1–96 |
| `master_mix_volume` | number | 25 | µL per well |
| `sample_volume` | number | 5 | µL per well |
| `total_volume` | number | 50 | µL total per well; used for water top-up |

---

### `rt_normalization`

Normalizes RNA sample concentrations to a target before reverse transcription.

```json
{
  "num_samples":          24,
  "target_concentration": 50,
  "final_volume":         20,
  "sample_concentrations": [120, 85, 60, "..."]
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `num_samples` | int | 24 | 1–96 |
| `target_concentration` | number | 50 | ng/µL |
| `final_volume` | number | 20 | µL final per well |
| `sample_concentrations` | list[number] | (uniform 100 ng/µL) | One value per sample; omit for equal-volume |

---

## Environment requirements

### OT_VENV_PYTHON

`simulate_protocol` shells out to `opentrons_simulate`. Because the `opentrons` package conflicts with FastMCP (pydantic / anyio version clash), it **must** run inside a separate virtualenv.

Set in `.env`:

```
OT_VENV_PYTHON=C:/path/to/venv_ot/Scripts/python.exe
```

If this variable is absent the tool falls back to `sys.executable` (which will likely fail with an ImportError).

### Setup (one-time)

```powershell
python -m venv venv_ot
.\venv_ot\Scripts\Activate.ps1
pip install opentrons
```

Then add the full path to `venv_ot\Scripts\python.exe` in `.env`.

---

## Output artefacts

All outputs land under `output/<run_id>/` relative to the working directory.

| File | Description |
|------|-------------|
| `report.pdf` | Multi-page PDF: cover, initial/final deck states, per-plate heatmaps, step log table |
| `dashboard.html` | Self-contained Plotly HTML with animated plate heatmaps and play/pause slider |
| `deck_animation.gif` | Animated GIF stepping through every deck snapshot at 2 fps |
| `stats_dashboard.png` | 4-panel matplotlib figure: volume per slot, action breakdown, tip timeline, well activity heatmap |

---

## Heuristic detectors (analyze_protocol)

| Detector | What it flags |
|----------|--------------|
| `tip_waste` | Tips discarded after a single transfer when reuse is safe |
| `volume_overflow` | Dispense volumes that would exceed well capacity |
| `empty_aspirate` | Aspirating from a well with insufficient volume |
| `pipette_range` | Transfer volumes outside the pipette's accurate range |
| `batchable_transfers` | Repeated single-well transfers that could be batched |
| `tip_rack_exhaustion` | Protocol would exhaust available tips |

Each recommendation includes `issue`, `severity` (low/medium/high), `description`, and `suggestion`.

---

## Labware names (for protocol generation)

Common values the generator accepts:

- `corning_96_wellplate_360ul_flat`
- `biorad_96_wellplate_200ul_pcr`
- `opentrons_96_wellplate_200ul_pcr_full_skirt`
- `opentrons_96_tiprack_300ul`
- `opentrons_96_tiprack_20ul`
- `opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap`

---

## Example conversation flow

**User:** Set up a 1:2 serial dilution with 8 steps and 100 µL starting volume.

**Model:** Call `run_full_pipeline` with:
```json
{
  "task_type": "serial_dilution",
  "parameters_json": "{\"num_dilutions\": 8, \"dilution_factor\": 2, \"initial_volume\": 100}"
}
```

The tool returns file paths for the PDF, HTML dashboard, GIF, and stats PNG. Summarize the recommendations and output paths for the user.
