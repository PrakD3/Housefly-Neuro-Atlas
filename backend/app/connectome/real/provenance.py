"""
Dataset provenance tracking for the real connectome provider.

Every result from the real provider carries traceable provenance so
that:
  1. Results can never be confused with synthetic test data.
  2. The exact dataset/version that produced a result is always known.

Provenance fields follow the Phase 3 specification:
  dataset       — dataset identifier (e.g., "male-cns:v1.0")
  version       — version string extracted from dataset identifier
  source        — official source institution / project
  provider      — programmatic access method
  access_method — how data was retrieved (e.g., "neuPrint REST API")
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class DatasetProvenance:
    """
    Immutable provenance record for a connectome dataset.

    This record is attached to the real provider and surfaced through
    the ConnectomeMetadata response so the UI can display the correct
    dataset identity.
    """
    dataset_id: str           # e.g., "male-cns:v1.0"
    dataset_name: str         # e.g., "Drosophila Male CNS"
    dataset_version: str      # e.g., "v1.0"
    organism: str             # e.g., "Drosophila melanogaster"
    sex: str                  # e.g., "male"
    source_institution: str   # e.g., "HHMI Janelia Research Campus"
    source_url: str           # e.g., "https://neuprint.janelia.org"
    access_method: str        # e.g., "neuPrint REST API"
    license: str              # e.g., "CC-BY 4.0"
    citation: str             # primary citation for this dataset


# ---------------------------------------------------------------------------
# Official provenance record for male-cns:v1.0
# ---------------------------------------------------------------------------
#
# Source: https://neuprint.janelia.org
# Dataset: male-cns:v1.0
# Access date for this record: 2026-09-23
# License: CC-BY 4.0
# Collaborators: HHMI Janelia FlyEM, University of Cambridge,
#                MRC Laboratory of Molecular Biology, Google Research
#
MALE_CNS_V1_PROVENANCE = DatasetProvenance(
    dataset_id="male-cns:v1.0",
    dataset_name="Drosophila Male CNS",
    dataset_version="v1.0",
    organism="Drosophila melanogaster",
    sex="male",
    source_institution=(
        "HHMI Janelia Research Campus (FlyEM Project Team); "
        "University of Cambridge; MRC Laboratory of Molecular Biology; "
        "Google Research"
    ),
    source_url="https://neuprint.janelia.org",
    access_method="neuPrint REST API — POST /api/custom/custom (Cypher queries)",
    license="CC-BY 4.0",
    citation=(
        "Janelia FlyEM Project Team et al. "
        "Drosophila Male CNS connectome (male-cns:v1.0). "
        "HHMI Janelia Research Campus. https://neuprint.janelia.org"
    ),
)
