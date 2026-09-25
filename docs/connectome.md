# Connectome Architecture — Drosophila-NeuroAtlas

> This document describes the connectome data architecture, visualization pipeline,
> and real vs synthetic mode behavior as of Phase 4.

---

## Data Flow

```text
ConnectomeProvider (abstract)
        ↓
SyntheticConnectomeProvider   or   RealDrosophilaConnectomeProvider
        ↓                                    ↓
  In-memory graph                     neuPrint REST API
        ↓                                    ↓
Bounded Subgraph Response       Bounded Subgraph Response
        ↓                                    ↓
              ← Normalized Neuron / Connection models →
                              ↓
                    Backend API (/connectome/...)
                              ↓
                     Frontend API client
                              ↓
               VisualizationTransform (render-only)
                              ↓
                    Three.js / React Three Fiber
```

---

## Provider Architecture

The system uses a provider abstraction (`ConnectomeProvider`) that separates
the application from the specific data source. The active provider is selected
at startup via the `CONNECTOME_PROVIDER` environment variable.

### Switching Providers

| Variable             | Value       | Effect                                 |
|----------------------|-------------|----------------------------------------|
| `CONNECTOME_PROVIDER`| `synthetic` | Uses `SyntheticConnectomeProvider`     |
| `CONNECTOME_PROVIDER`| `real`      | Uses `RealDrosophilaConnectomeProvider`|

The provider is created once as a singleton and reused for the lifetime of
the process. See `backend/app/connectome/factory.py`.

### Real Provider Requirements

When `CONNECTOME_PROVIDER=real`:

- `NEUPRINT_TOKEN` must be set (obtain from https://neuprint.janelia.org)
- `NEUPRINT_BASE_URL` defaults to `https://neuprint.janelia.org`
- `NEUPRINT_DATASET` defaults to `male-cns:v1.0`

If the token is missing, `NeuPrintAuthenticationError` is raised and surfaced
as HTTP 503 to the frontend with a clear error message.

---

## Bounded Subgraph Architecture

The browser **never** receives the entire MaleCNS connectome.

All real-data visualization works through bounded server-side queries:

1. User enters a neuron body ID in the frontend
2. Frontend calls `GET /connectome/neighborhood?neuron_id=<id>&hops=<n>`
3. Backend retrieves the neuron and its N-hop neighborhood from the provider
4. Server enforces hard limits:
   - **MAX_SUBGRAPH_NEURONS = 500** (default)
   - **MAX_SUBGRAPH_CONNECTIONS = 2000** (default)
5. Truncated results set `was_truncated=true`
6. Response includes provenance metadata (dataset, version, timestamp)
7. Frontend renders only the returned bounded subgraph

### Safety Limits

These are software engineering defaults, not scientific claims about
meaningful subgraph sizes:

| Parameter          | Default | Maximum | Purpose                        |
|--------------------|---------|---------|--------------------------------|
| `max_neurons`      | 500     | 500     | Protect browser rendering      |
| `max_connections`  | 2000    | 2000    | Prevent browser memory overload|
| `hops`             | 1       | 2       | Limit expansion radius         |

---

## Coordinate Handling

### Critical Rules

1. **Real coordinates are never fabricated.** When neuPrint does not provide
   `somaLocation` for a neuron, `x`, `y`, `z` are `null` and
   `has_coordinates` is `false`.

2. **Null coordinates are never defaulted to (0, 0, 0).**

3. **Neurons without coordinates are not rendered in 3D space.** The
   `NeuronNode` and `ConnectionLine` components gate on `scenePosition`
   being non-null.

4. **The distinction between anatomical coordinates and visualization
   coordinates is always preserved.**

### Coordinate Pipeline

```text
Raw Anatomical Coordinates (voxel space, 8 nm/voxel)
    e.g. x=150000, y=200000, z=80000
         ↓
    has_coordinates = true
         ↓
    VisualizationTransform.computeTransform()
         — computes bounding box center and scale factor
         ↓
    toScenePosition()
         — maps to Three.js scene coordinates (e.g. [-25, 25] range)
         ↓
    Three.js rendering

    OR

    somaLocation absent
         ↓
    x=null, y=null, z=null
    has_coordinates = false
         ↓
    toScenePosition() returns null
         ↓
    NeuronNode / ConnectionLine returns null (not rendered)
```

### Visualization Transform

The `VisualizationTransform` module (`VisualizationTransform.ts`) performs a
**render-only** coordinate transformation:

- Computes the bounding box of all neurons with valid coordinates
- Centers the bounding box at the Three.js origin
- Scales the coordinates to fit within a target scene diameter (default: 50 units)

**This transform never modifies the original Neuron data model.**

The original anatomical coordinates are preserved in the Neuron objects and
displayed in the inspector panel.

---

## Real vs Synthetic Mode

### Synthetic Mode (`CONNECTOME_PROVIDER=synthetic`)

- 100 neurons with deterministic positions in a bilateral brain-like layout
- All neurons have coordinates (`has_coordinates=true`)
- Full graph loaded into memory on startup
- Client-side filtering by cell type, region, search query
- No network requests to external services

### Real Mode (`CONNECTOME_PROVIDER=real`)

- Backed by HHMI Janelia MaleCNS v1.0 through neuPrint REST API
- Neurons loaded on-demand via bounded neighborhood queries
- Some neurons may lack coordinates (`has_coordinates=false`)
- Results cached per-provider-instance with bounded LRU cache
- Authentication required (Bearer token)
- All responses include provenance metadata

### UI Indicators

| Mode      | Header Badge         | Footer Badge  | Left Panel Status      |
|-----------|---------------------|---------------|------------------------|
| Synthetic | `SYNTHETIC DATA`    | `SYNTHETIC`   | `Software Test Data`   |
| Real      | `REAL CONNECTOME`   | version (e.g. `v1.0`) | `Real Connectome Data` |

The badge is driven by the backend's `ConnectomeMetadata.is_synthetic` field.
It is never hard-coded independently of backend state.

---

## Error Handling

The frontend handles the following error states explicitly:

| Error                     | HTTP Code | UI Display                     |
|--------------------------|-----------|-------------------------------|
| Provider unavailable     | 503       | "REAL CONNECTOME UNAVAILABLE" |
| Authentication failure   | 503       | Token instruction message     |
| Neuron not found         | 404       | "NEURON NOT FOUND"            |
| Empty subgraph           | 200       | "No Subgraph Loaded" prompt   |
| Network failure          | N/A       | Generic error panel           |
| Backend unreachable      | N/A       | "System Disconnected" screen  |

**The system never silently falls back from real to synthetic mode.**

---

## API Endpoints

### Visualization-critical endpoints (Phase 4)

| Method | Path                                  | Response Model             | Purpose                                |
|--------|---------------------------------------|---------------------------|----------------------------------------|
| GET    | `/connectome/info`                    | `ConnectomeMetadata`      | Dataset identity and provider type     |
| GET    | `/connectome/neighborhood`            | `BoundedSubgraphResponse` | Bounded subgraph for visualization     |
| GET    | `/connectome/search`                  | `List[Neuron]`            | Search neurons by ID/type/instance     |
| GET    | `/connectome/neurons/{neuron_id}`     | `Neuron`                  | Single neuron lookup                   |

### Other endpoints (Phase 1–3)

| Method | Path                                         | Response Model      |
|--------|----------------------------------------------|---------------------|
| GET    | `/connectome/neurons`                        | `List[Neuron]`      |
| GET    | `/connectome/neurons/{id}/neighbors`         | `SubgraphResponse`  |
| POST   | `/connectome/subgraph`                       | `SubgraphResponse`  |
| GET    | `/health`                                    | `HealthResponse`    |

---

## Performance

### Design Decisions

1. **No full connectome download.** The MaleCNS contains ~100K+ neurons.
   The browser never receives more than 500 neurons per query.

2. **Server-side subgraph construction.** All graph traversal and
   subgraph extraction happens in the backend.

3. **LRU caching.** The real provider caches neuron lookups and
   connection queries per-instance (max 512 entries).

4. **Canvas key rotation.** When the subgraph changes, the Three.js
   Canvas is remounted via key change to ensure clean geometry disposal.

5. **Lazy provider initialization.** The provider singleton is created
   on first request, not at import time.

---

## Limitations

- The visualization shows **structural** connectome data and metadata only.
  No neural activity simulation, perturbation modeling, or behavioral
  prediction is performed in Phase 4.

- Not all real neurons have soma coordinates. Neurons without coordinates
  are not visible in the 3D scene.

- The visualization does not represent the entire MaleCNS connectome.
  It shows bounded subgraphs centered on user-selected neurons.

- Connection line thickness in the visualization does not automatically
  represent biological synapse count unless explicitly documented.

---

## Data Source

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Dataset        | male-cns:v1.0                                        |
| Organism       | *Drosophila melanogaster*                            |
| Sex            | Male                                                 |
| Source          | HHMI Janelia Research Campus (FlyEM Project Team)    |
| URL            | https://neuprint.janelia.org                         |
| Access method  | neuPrint REST API (POST /api/custom/custom, Cypher)  |
| License        | CC-BY 4.0                                            |

See `docs/data_sources.md` for additional provenance details.
