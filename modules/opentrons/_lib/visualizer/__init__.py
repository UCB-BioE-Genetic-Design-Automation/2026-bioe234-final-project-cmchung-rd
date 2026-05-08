"""
OT-2 simulation log visualizer package (Christian Chung).
"""

from .log_parser import parse_log, ParsedProtocol, PipettingStep
from .state_tracker import build_snapshots, DeckSnapshot, is_tracked_plate
from .deck_visualizer import render_deck_snapshot, render_all_steps, create_gif, create_mp4
from .plate_visualizer import render_plate, render_well_timeseries
from .report_generator import generate_report
from .stats_visualizer import render_stats_dashboard
from .html_exporter import export_html

__all__ = [
    "parse_log", "ParsedProtocol", "PipettingStep",
    "build_snapshots", "DeckSnapshot", "is_tracked_plate",
    "render_deck_snapshot", "render_all_steps", "render_plate", "render_well_timeseries",
    "create_gif", "create_mp4",
    "generate_report", "render_stats_dashboard", "export_html",
]
