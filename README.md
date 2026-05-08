# LLM-Driven Optimization and Visualization of Opentrons OT-2 Protocols

**BIOE 234 Final Project — Spring 2026**

A conversational AI system that lets you describe a lab protocol in plain English and automatically generates an Opentrons OT-2 Python script, simulates it, identifies optimization opportunities via heuristic analysis, and produces rich visualizations — all through a single chat interface.

---

## Team

| Member | Role | Module |
|--------|------|--------|
| Taylor Elliott | Protocol Generation | `generate_protocol` |
| Adriann Brodeth | Simulation Engine | `simulate_protocol` |
| Alex Haynes | Heuristic Analysis | `analyze_protocol` |
| Christian Chung | Visualization | `visualize_deck_state` |
| Joshua Yap | MCP Server Integration | `run_full_pipeline` + tool wiring |

---

## What it does

**User types:** *"Set up a 1:2 serial dilution with 8 steps and 100 µL starting volume."*

The pipeline automatically:

1. **Generates** a complete OT-2 Python protocol script tailored to the task
2. **Simulates** it with `opentrons_simulate` (dry-run, no robot needed)
3. **Analyzes** the simulation log with 6 heuristic detectors for tip waste, volume overflow, empty aspirate, pipette range mismatches, batchable transfers, and tip rack exhaustion
4. **Visualizes** the results as four artefacts:
   - Multi-page **PDF report** (cover, deck snapshots, per-plate heatmaps, step log table)
   - Interactive **Plotly HTML dashboard** with animated plate heatmaps
   - **GIF animation** stepping through every deck state
   - **Statistics PNG** (volume per slot, action breakdown, tip timeline, well activity heatmap)

---

## Supported protocol types

| `task_type` | Description |
|-------------|-------------|
| `serial_dilution` | Multi-step fold dilution across 96-well plate columns |
| `pcr_setup` | Master mix + sample dispensing for PCR plates |
| `rt_normalization` | RNA concentration normalization before reverse transcription |

---

## Architecture

```
streamlit run app.py
        │
        ├── Gemini 2.5 Flash (function-calling)
        │         │
        │         └── run_ot2_pipeline (tool declaration in app.py)
        │                   │
        │                   └── modules/opentrons/_lib/
        │                             ├── generator.py
        │                             ├── simulation_engine.py
        │                             ├── analyzer.py
        │                             └── visualizer/
        │
        └── ~/Downloads/OT2_outputs/<run_id>/
                  ├── report.pdf
                  ├── dashboard.html
                  ├── deck_animation.gif
                  └── stats_dashboard.png
```

The MCP server (`server.py`) and terminal client (`client_gemini.py`) also exist for headless/CLI use. The Streamlit app (`app.py`) is the primary interface for end users.

Internal libraries live in `modules/opentrons/_lib/`:

```
_lib/
  generator.py
  simulation_engine.py
  analyzer.py
  recommendation.py
  heuristics/
  visualizer/
    log_parser.py
    state_tracker.py
    deck_visualizer.py
    plate_visualizer.py
    html_exporter.py
    report_generator.py
    stats_visualizer.py
```

---

## Setup

### Prerequisites

- Python 3.10 or newer ([python.org](https://python.org))
- A free Google Gemini API key — [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys) (sign in with UC Berkeley Google account)

### Windows (recommended) — double-click setup

1. Clone or download this repo
2. Double-click **`setup.bat`** — creates both virtual environments and configures `.env` automatically
3. Open `.env` and paste your Gemini API key: `GEMINI_API_KEY="your_key_here"`
4. Double-click **`launch.bat`** to start the web app

### Manual setup (Mac/Linux or if setup.bat fails)

```bash
# Main venv
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
pip install -r requirements.txt

# Opentrons venv (separate — avoids pydantic/anyio conflict with FastMCP)
python -m venv venv_ot
./venv_ot/bin/pip install opentrons
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY="your_key_here"
OT_VENV_PYTHON="/full/path/to/venv_ot/bin/python"
```

Then run the app:
```bash
source .venv/bin/activate
streamlit run app.py --server.headless true
```

---

## Running

**Windows:** double-click `launch.bat`

**Mac/Linux / manual:**
```bash
source .venv/bin/activate
streamlit run app.py --server.headless true
```

Then open **http://localhost:8501** in your browser. Type a protocol description in the chat box and hit Enter.

---

## Example prompts

### Serial Dilution

```
Generate and simulate an Opentrons OT-2 protocol for a 1:10 serial dilution
across one row of a 96-well plate. Start with 200 µL of sample in the first
well and dilute 1:10 across 8 wells using 20 µL transfers into 180 µL of
diluent. Use a P300 single-channel pipette and change tips between transfers.
```

**Expected output:** ~50 simulation steps, 8 deck snapshots, PDF + HTML dashboard + GIF + stats PNG downloaded to `~/Downloads/OT2_outputs/`.

---

### PCR Setup

```
Create a protocol to set up a 24-sample PCR reaction on an OT-2. Each well
should receive 25 µL of master mix from a 2 mL tube followed by 5 µL of
sample from a 96-well sample plate. Use a P300 multi-channel pipette for
master mix and a P20 single-channel pipette for samples. Change tips between
samples.
```

**Expected output:** ~100 simulation steps, PDF report with per-plate volume heatmaps, optimization recommendations if any tip-waste or pipette-range issues are detected.

---

### RNA Normalization

```
Normalize 24 RNA samples to 50 ng/µL in a final volume of 20 µL for reverse
transcription. Source concentrations range from 100–500 ng/µL.
```

---

## Running tests

```powershell
pytest -vv -l
```

Tests cover:
- `seq_basics` example tools (reverse complement, translate)
- `generate_protocol` — script generation for all task types, error handling
- `analyze_protocol` — recommendation structure, empty log edge case

Simulation and visualization tests require the Opentrons venv and are best run manually.

---

## Output files

All outputs are written to `~/Downloads/OT2_outputs/<run_id>/` (auto-created, excluded from git):

| File | Description |
|------|-------------|
| `report.pdf` | Multi-page PDF: cover page, initial/final deck states, per-plate heatmaps before/after, full step log table |
| `dashboard.html` | Self-contained interactive HTML; animated 96-well plate heatmaps with play/pause slider |
| `deck_animation.gif` | Animated GIF cycling through deck snapshots at 2 fps |
| `stats_dashboard.png` | 4-panel figure: volume dispensed per slot, action type breakdown, tip usage timeline, well activity heatmap |

---

## Heuristic detectors

`analyze_protocol` runs 6 independent detectors on the simulation log:

| Detector | Issue flagged |
|----------|--------------|
| `tip_waste` | Tips discarded after a single use when reuse is safe |
| `volume_overflow` | Dispense would exceed well maximum volume |
| `empty_aspirate` | Aspirating from a well with insufficient volume |
| `pipette_range` | Transfer volume outside the pipette's accurate operating range |
| `batchable_transfers` | Repeated single-well transfers that could be combined |
| `tip_rack_exhaustion` | Protocol would use more tips than are loaded |

Each recommendation includes `issue`, `severity` (low/medium/high), `description`, and `suggestion`.

---

## Framework notes

This project is built on the **BioE234 MCP Starter** framework. The framework auto-discovers tools by scanning `modules/<name>/tools/` for `.py` + `.json` file pairs and registers them as MCP tools without any boilerplate.

Key conventions:
- Each tool is a **Function Object** class with `initiate()` (one-time setup) and `run()` (per-call logic)
- A module-level alias `tool_name = _instance.run` exposes the function for direct import and testing
- A companion `.json` file declares the tool's schema, description, and parameters
- `SKILL.md` injects domain knowledge into Gemini's system prompt at startup

See `modules/seq_basics/` for a minimal worked example of the pattern.

---

## Understanding "Note" steps

If your PDF report or statistics chart contains steps labelled **"Note"**, it means the simulation log contained lines that the visualizer's parser could not classify as a known pipetting action (aspirate, dispense, pick-up tip, etc.).

Common causes:
- The generated script uses a non-standard labware name not in the parser's vocabulary
- The protocol includes custom or module-specific commands (e.g. thermocycler profiles) that produce unusual log lines
- Opentrons printed a calibration or runtime warning that slipped through the skip-list

**How to fix:** These steps are cosmetic — they do not affect the simulation or heuristic analysis. If they bother you, you can re-run with a simpler prompt that avoids uncommon labware names, or open `modules/opentrons/_lib/visualizer/log_parser.py` and add the offending line pattern to `RE_SKIP_LINE`.

---

## Troubleshooting

**`simulate_protocol` returns an error about opentrons not found**  
Check that `OT_VENV_PYTHON` in `.env` points to the correct Python executable inside `venv_ot`.

**Gemini 503 / quota error**  
The free Gemini tier has rate limits. Wait 30 seconds — the client retries automatically.

**`ModuleNotFoundError` on startup**  
Make sure `.venv` is activated before running `streamlit run app.py`.

**GIF export fails**  
Install Pillow: `pip install Pillow`. For MP4 export also install `imageio[ffmpeg]`.

**HTML dashboard shows "no tracked plates"**  
The log parser looks for standard Opentrons 96-well plate labware names. Verify the generated script uses a recognized labware identifier (see `modules/opentrons/SKILL.md`).

**Second pipeline run gives an error in the same browser session**  
This should be fixed in the current version (run IDs now use millisecond timestamps). If it still happens, click **🔄 New session** in the sidebar or refresh the page.

---
