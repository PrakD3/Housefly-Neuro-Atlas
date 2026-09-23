"""
Raw data-transfer objects (DTOs) for neuPrint REST API responses.

These types describe the EXTERNAL neuPrint schema and must NOT be
exposed beyond the real provider package.  The provider normalizes
these into the application's internal models (app.models.connectome).

Source:
  API: https://neuprint.janelia.org
  Spec: https://neuprint.janelia.org/api/help/swagger.yaml
  Dataset: male-cns:v1.0
  License: CC-BY 4.0

The /api/custom/custom endpoint returns:
  {
    "columns": ["col1", "col2", ...],
    "data": [[val1, val2, ...], ...]
  }

Neuron node properties available in male-cns:v1.0 (documented fields):
  bodyId         int     — unique neuron identifier
  type           str     — cell type classification (e.g., "DNge104")
  instance       str     — specific instance name
  superClass     str     — high-level classification
  class          str     — intermediate classification
  status         str     — annotation status (e.g., "Traced")
  predictedNt    str     — predicted neurotransmitter (e.g., "acetylcholine")
  somaLocation   list    — [x, y, z] voxel coordinates (8 nm/voxel); absent for some neurons

ConnectsTo relationship properties:
  weight         int     — synapse count between two bodies
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class NeuPrintCustomResponse:
    """Raw response from POST /api/custom/custom."""
    columns: List[str]
    data: List[List[Any]]


@dataclass
class NeuPrintNeuronRecord:
    """
    Normalized raw record for a single neuron from neuPrint.

    All fields are Optional to accommodate partial neuPrint responses.
    Coordinates are kept as Optional[float] — NEVER substituted with defaults.
    """
    body_id: int
    type: Optional[str] = None
    instance: Optional[str] = None
    super_class: Optional[str] = None
    status: Optional[str] = None
    predicted_nt: Optional[str] = None
    # somaLocation [x, y, z] — None when absent in source
    soma_x: Optional[float] = None
    soma_y: Optional[float] = None
    soma_z: Optional[float] = None

    @property
    def has_soma_location(self) -> bool:
        """True only when all three soma coordinates are present."""
        return (
            self.soma_x is not None
            and self.soma_y is not None
            and self.soma_z is not None
        )


@dataclass
class NeuPrintConnectionRecord:
    """Normalized raw record for a directed connection between two bodies."""
    source_body_id: int
    target_body_id: int
    weight: float
