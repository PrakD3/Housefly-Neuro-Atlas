# Drosophila-NeuroAtlas

> A connectome-driven computational platform for mapping chemical compounds to molecular targets, Drosophila neurons, neural circuits, and simulated behavioral outputs using graph-based computational models and interactive 3D visualization.

## Overview

**Drosophila-NeuroAtlas** is an open-source research project exploring how molecular perturbations can be traced through the nervous system of *Drosophila melanogaster*.

The project uses the publicly available Drosophila connectome as its biological foundation and combines:

- Chemical informatics
- Molecular target analysis
- Molecular docking
- Drosophila biological mapping
- Connectomics
- Graph-based neural-network analysis
- Computational perturbation
- Behavioral modeling
- Interactive 3D visualization

The goal is to create an interpretable computational environment where a researcher can start with a chemical compound or formulation and investigate how its potential molecular effects could propagate through real neural circuitry.

---

## Core Concept

```text
Chemical / Formulation
          ↓
    Molecular Structure
          ↓
     Target Analysis
          ↓
 Molecular Interaction
          ↓
 Drosophila Target Mapping
          ↓
   Real Connectome
          ↓
 Relevant Neural Subnetwork
          ↓
 Computational Perturbation
          ↓
 Neural Network Propagation
          ↓
    Circuit Response
          ↓
   Behavioral Proxy
          ↓
   Interactive 3D View
```

---

## Current Status

| Phase | Description                        | Status    |
|-------|------------------------------------|-----------|
| 0     | Project Foundation                 | ✅ Complete |
| 1     | Synthetic Connectome Engine        | ✅ Complete |
| 2     | 3D Synthetic Connectome Visualization | ✅ Complete |
| 3     | Real Drosophila Connectome Provider | ✅ Complete |
| 4     | Real Connectome Visualization      | ✅ Complete |
| 5+    | Neural Perturbation, Analysis, Chemistry… | Planned |

**Phase 4 — Real Connectome Visualization** enables interactive 3D exploration
of bounded subgraphs from the HHMI Janelia MaleCNS v1.0 connectome.

---

## Running the Application

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv/Scripts/activate   # Windows
# or: source .venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -e ".[dev]"

# Run in synthetic mode (no credentials needed)
set CONNECTOME_PROVIDER=synthetic
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Real mode** (requires neuPrint token):

```bash
set CONNECTOME_PROVIDER=real
set NEUPRINT_TOKEN=<your-token-from-neuprint.janelia.org>
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Running Tests

```bash
# Backend
python -m pytest backend/tests -v

# Frontend
cd frontend
npm test -- --run

# Frontend build verification
npm run build
```

---

## Connectome Modes

### Synthetic Mode (default)

- Uses a deterministic randomly-generated graph for development
- 100 neurons with bilateral brain-like spatial layout
- All neurons have 3D coordinates
- No external credentials required
- Clearly labeled as **SYNTHETIC DATA** in the UI

### Real Mode

- Uses the HHMI Janelia MaleCNS v1.0 dataset via neuPrint REST API
- Bounded subgraph queries (max 500 neurons, 2000 connections per request)
- Real neuron body IDs, cell types, neurotransmitters, and soma coordinates
- Neurons without somaLocation are never assigned fabricated coordinates
- Clearly labeled as **REAL CONNECTOME** in the UI

See [docs/connectome.md](docs/connectome.md) for detailed architecture.

---

## Real Connectome Data Source

| Field     | Value                                                |
|-----------|------------------------------------------------------|
| Dataset   | male-cns:v1.0                                        |
| Organism  | *Drosophila melanogaster*                            |
| Sex       | Male                                                 |
| Source    | HHMI Janelia Research Campus (FlyEM Project Team)    |
| URL       | https://neuprint.janelia.org                         |
| License   | CC-BY 4.0                                            |

See [docs/data_sources.md](docs/data_sources.md) for provenance details.

---

## Scientific Boundaries

This platform is under active development. As of Phase 4:

- The visualization shows **structural connectome data** only
- **No neural activity simulation** is performed
- **No behavioral prediction** is made
- **No toxicity modeling** is implemented
- Missing coordinates are preserved as absent, never fabricated
- Visualization transforms are rendering-only and do not represent anatomical truth

---

## License

MIT