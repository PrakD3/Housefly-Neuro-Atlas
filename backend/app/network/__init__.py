"""
Network Analysis Package for Drosophila-NeuroAtlas Phase 6.

Exposes:
- NetworkAnalysisEngine
- Structural and Dynamic analysis functions
- Safety constants
"""
from .centrality import compute_centrality_metrics
from .engine import (
    MAX_ANALYSIS_EDGES,
    MAX_ANALYSIS_NODES,
    MAX_PATH_LENGTH,
    NetworkAnalysisEngine,
)
from .metrics import compute_structural_metrics
from .paths import compute_target_analysis
from .perturbation import compute_perturbation_analysis
from .temporal import compute_temporal_metrics

__all__ = [
    "NetworkAnalysisEngine",
    "compute_structural_metrics",
    "compute_centrality_metrics",
    "compute_target_analysis",
    "compute_temporal_metrics",
    "compute_perturbation_analysis",
    "MAX_ANALYSIS_NODES",
    "MAX_ANALYSIS_EDGES",
    "MAX_PATH_LENGTH",
]
