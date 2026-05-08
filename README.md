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

**Expected output:** ~75 simulation steps, per-sample volume heatmap, likely a `pipette_range` recommendation if any water volumes fall below 20 µL.

---

### Reagent Plate Stamping

```
Stamp 50 µL of PBS from a 12-well reservoir in slot 3 into all 96 wells of a
flat-bottom plate in slot 2. Use a P300 8-channel multi-channel pipette and
change tips between each row.
```

**Expected output:** ~30 simulation steps, uniform volume heatmap across all 96 wells, likely a `tip_waste` recommendation since tips could be reused between rows.

---

### Compound Spotting (Triplicates)

```
Spot 2 µL of 8 different compounds from tubes A1 through A8 in a 24-tube rack
into triplicate wells on a 96-well PCR plate. Compounds go into rows A–H,
columns 1–3 (A1:A3, B1:B3, C1:C3, D1:D3, E1:E3, F1:F3, G1:G3, H1:H3).
Use a P20 single-channel pipette with a fresh tip for each compound.
```

**Expected output:** ~25 simulation steps, heatmap showing 3 filled columns with compound groupings, `batchable_transfers` recommendation since each compound visits 3 identical wells.

---

### ELISA Plate Setup

```
Set up an ELISA plate with the following steps on an OT-2:
1. Dispense 100 µL of coating antibody (from a reservoir in slot 3) into all
   96 wells of a flat-bottom plate in slot 2 using a P300 8-channel pipette,
   changing tips between rows.
2. Dispense 50 µL of each of 8 standard curve concentrations (from columns 1–8
   of a source plate in slot 4) into duplicate wells (columns 1–2, 3–4, etc.)
   of the destination plate using a P300 single-channel pipette with fresh tips
   per standard.
3. Dispense 50 µL of 16 unknown samples (from a source plate in slot 5) into
   the remaining wells using a P300 single-channel pipette with fresh tips.
```

**Expected output:** ~130 simulation steps across 3 labware sources, multi-stage heatmap showing antibody coat + standards + samples, likely `batchable_transfers` for the standards.

---

### Pooling From a Full Plate

```
Pool 10 µL from every well in column 1 of a 96-well plate in slot 2 into
well A1 of a 12-well reservoir in slot 5. Then pool column 2 into A2, and
so on through column 12 into A12. Use a P20 single-channel pipette with a
fresh tip per well.
```

**Expected output:** ~100 simulation steps (8 wells × 12 columns), source plate heatmap depleting uniformly, destination reservoir showing 12 pools building up.

---

### Dose-Response Assay Setup

```
Set up a 10-point dose-response assay on an OT-2 for 8 compounds in duplicate.
Plate layout: columns 1–10 are concentrations (10-fold serial dilution starting
from 100 µM), columns 11–12 are positive and negative controls. Source plate
in slot 3 has compounds at 100 µM in rows A–H. Dilution plate in slot 4 is
empty. Destination assay plate in slot 2 is empty.

Steps:
1. Add 180 µL of DMSO from reservoir in slot 5 into columns 2–10 of the
   dilution plate using a P300 single-channel pipette, one tip per column.
2. Transfer 20 µL from column 1 of the source plate into column 1 of the
   dilution plate (fresh tip per well).
3. Perform a 1:10 serial dilution from column 1 to column 10 of the dilution
   plate — transfer 20 µL, mix 5 times, then move to the next column. Change
   tips between columns.
4. Stamp 2 µL from each column of the dilution plate into the corresponding
   column of the assay plate using a P20 single-channel pipette, fresh tip
   per well.
```

**Expected output:** ~200 simulation steps, GIF showing 3-plate workflow (source → dilution → assay), gradient concentration heatmap on dilution plate, `empty_aspirate` warning possible at the lowest dilution point.

---

### DNA Library Normalization and Pooling

```
Normalize and pool 48 DNA libraries for sequencing on an OT-2:
1. Libraries are in columns 1–6 of a 96-well plate in slot 3 at varying
   concentrations (assume all are between 5–50 ng/µL).
2. Normalize each library to 4 ng/µL in 10 µL total volume in a fresh plate
   in slot 2 by adding water from a reservoir in slot 4 first, then library.
   Use a P20 single-channel pipette with fresh tips for water and for each
   library.
3. After normalization, pool 5 µL from each well of columns 1–6 of the
   destination plate into a single tube in position A1 of a tube rack in
   slot 5. Use a P20 single-channel pipette with fresh tips.
```

**Expected output:** ~150 simulation steps, source plate depleting non-uniformly (higher-concentration libraries contribute less volume), normalized destination plate with uniform fill, `pipette_range` recommendation if any water or library volumes fall below 2 µL.

---

### Cell Viability Assay (Sequential Reagent Addition)

```
Automate a cell viability assay on a 96-well flat-bottom plate in slot 2
containing cells:
1. Remove 50 µL of media from every well using a P300 8-channel pipette
   (discard into a waste reservoir in slot 9). Change tips between rows.
2. Add 100 µL of treatment compounds: columns 1–3 get compound A (from slot 3),
   columns 4–6 get compound B (from slot 4), columns 7–9 get compound C
   (from slot 5), columns 10–12 are vehicle control (DMSO from slot 6).
   Use a P300 8-channel pipette, change tips between compound groups.
3. Add 10 µL of CellTiter-Glo reagent from a reservoir in slot 7 to all 96
   wells using a P20 8-channel pipette, same tip for all dispenses.
4. Mix each well 3 times with 50 µL using the P300 8-channel pipette,
   changing tips between rows.
```

**Expected output:** ~120 simulation steps across 4 distinct liquid-handling stages, heatmap showing 4 treatment zones across the plate, `tip_waste` recommendation for the CellTiter-Glo step (same-tip dispense could extend to mixing too).

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

## Limitations and future work

| Area | Current limitation | What would fix it |
|------|--------------------|-------------------|
| **Protocol types** | Three hard-coded templates + free-form Gemini generation for custom protocols. Free-form can hallucinate invalid labware names or API calls. | Expand labware vocabulary; add a validation layer that checks generated scripts against the Opentrons labware library before simulating. |
| **Simulation only** | `opentrons_simulate` is a dry-run — it does not connect to a real OT-2 or check physical liquid levels. | Integrate with the Opentrons HTTP API for live robot execution and liquid-level sensing. |
| **Robot model** | OT-2 only (API level 2.15). The newer Opentrons Flex (OT-3) uses a different API and deck layout. | Add a robot-model selector and separate code-generation paths for Flex. |
| **Single pipette** | The template generator loads one pipette per protocol. Dual-pipette workflows (e.g. P20 + P300 simultaneously) are not supported in templates, only in free-form custom mode. | Extend the template parameter schema to support a second `pipette_right` instrument. |
| **Heuristic analysis** | The 6 detectors are rule-based and do not learn from protocol history or understand protocol intent. | Train a small ML model on real protocol logs to predict non-obvious waste patterns. |
| **Labware vocabulary** | The log parser and volume heuristics recognise ~15 common labware types. Unusual labware (custom plates, specialty reservoirs) may appear as unrecognised "Note" steps. | Maintain a full labware JSON catalogue and auto-update from the Opentrons labware repository. |
| **No multi-step / loop protocols** | Complex protocols with conditional branching, thermocycler loops, or heater-shaker steps are partially supported in free-form mode but not in templates. | Add template types for thermocycler PCR and heater-shaker mixing. |
| **LLM cost and latency** | Every custom protocol generation makes a Gemini API call. With a free-tier key this adds ~2–5 s and may hit rate limits. | Cache generated scripts by description hash; add a local LLM fallback (e.g. Ollama). |

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
