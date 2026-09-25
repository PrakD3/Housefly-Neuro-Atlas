# Drosophila-NeuroAtlas — AGENT MASTER SPECIFICATION

> This file is the master instruction and development reference for AI coding agents working on Drosophila-NeuroAtlas.
>
> READ THIS FILE BEFORE MODIFYING THE PROJECT.
>
> This file defines the project's purpose, architecture, development roadmap, engineering rules, scientific boundaries, and agent behavior.

---

# 1. AGENT OPERATING MODE

You are an engineering agent working on:

# Drosophila-NeuroAtlas

You are NOT being asked to build the entire project at once.

The project must be developed incrementally through clearly defined phases.

Before doing any work:

1. Read this file completely.
2. Inspect the current repository.
3. Determine what has already been implemented.
4. Identify the requested phase/task.
5. Understand the dependencies between components.
6. Implement only the requested scope.
7. Test the implementation.
8. Verify that existing functionality has not been broken.
9. Report what was completed.
10. STOP.

Do not automatically continue to the next phase.

The user will explicitly authorize the next phase.

---

# 2. CURRENT PROJECT STATUS

This section should be updated by the agent only when appropriate.

Current Phase:

PHASE 7 — CHEMICAL ENGINE

Current Task:

Not started. Waiting for explicit authorization.

Completed Phases:

PHASE 0 — PROJECT FOUNDATION
PHASE 1 — SYNTHETIC CONNECTOME ENGINE
PHASE 2 — 3D SYNTHETIC CONNECTOME VISUALIZATION
PHASE 3 — REAL DROSOPHILA CONNECTOME PROVIDER
PHASE 4 — REAL CONNECTOME VISUALIZATION
PHASE 5 — NEURAL PERTURBATION ENGINE
PHASE 6 — NETWORK ANALYSIS ENGINE

IMPORTANT:

Do not assume that the current phase is complete merely because files exist.

A phase is complete only when its acceptance criteria have been satisfied and verified.

---

# 3. PROJECT PURPOSE

Drosophila-NeuroAtlas is a connectome-driven computational neuroscience platform for investigating how molecular and chemical perturbations can propagate through a real Drosophila neural network.

The central concept is:

Chemical / Formulation
        ↓
Molecular Structure
        ↓
Molecular Targets
        ↓
Drosophila Biological Mapping
        ↓
Real Drosophila Connectome
        ↓
Relevant Neural Subnetwork
        ↓
Computational Perturbation
        ↓
Network Propagation
        ↓
Circuit Response
        ↓
Behavioral Proxy
        ↓
Interactive 3D Visualization

The project is based on real Drosophila connectomic data from the Google Research / HHMI Janelia ecosystem.

---

# 4. CORE RESEARCH QUESTION

The project investigates:

> Can experimentally supported molecular perturbations be mapped onto a real Drosophila connectome and computationally traced through neural circuits to generate interpretable behavioral hypotheses?

The project is therefore a multiscale computational system.

It connects:

MOLECULAR SCALE

to

NEURAL NETWORK SCALE

to

BEHAVIORAL SCALE.

---

# 5. CORE PHILOSOPHY

The project follows four principles:

## Real Data

Use real biological and connectomic data whenever available.

## Real Circuits

The neural network should be based on an actual Drosophila connectome rather than an invented neural network.

## Explicit Assumptions

Whenever experimental evidence is unavailable and a computational assumption is required, explicitly identify it as an assumption.

## Reproducibility

Experiments should record enough information to reproduce the computational result.

---

# 6. WHAT THIS PROJECT IS NOT

This project is NOT:

- A generic AI prediction platform.
- A black-box behavioral prediction model.
- A fake 3D brain visualization.
- A simple chemical toxicity classifier.
- A chatbot about neuroscience.
- A generic machine-learning demo.
- A system that invents biological relationships.
- A system that treats docking scores as experimental evidence.

Machine learning may be added later if scientifically justified.

However, the core architecture must remain interpretable and graph-based.

---

# 7. PRIMARY SCIENTIFIC ARCHITECTURE

The complete conceptual pipeline is:

USER
 ↓
FORMULATION ENGINE
 ↓
CHEMICAL ENGINE
 ↓
TARGET / EVIDENCE ENGINE
 ↓
DROSOPHILA BIOLOGICAL MAPPING
 ↓
CONNECTOME PROVIDER
 ↓
SUBNETWORK EXTRACTION
 ↓
PERTURBATION ENGINE
 ↓
NEURAL SIMULATION
 ↓
NETWORK ANALYSIS
 ↓
BEHAVIOR ENGINE
 ↓
3D VISUALIZATION

---

# 8. THREE COMPUTATIONAL SCALES

## 8.1 Molecular Scale

The molecular layer handles:

Compound
 ↓
SMILES / Structure
 ↓
Molecular Descriptors
 ↓
Targets
 ↓
Experimental / Computational Evidence

Primary tool:

RDKit

Potential future tools:

Molecular docking

Molecular dynamics

---

## 8.2 Neural Network Scale

The neural layer handles:

Molecular Target
 ↓
Relevant Drosophila Biological Entity
 ↓
Relevant Neurons
 ↓
Connectome
 ↓
Neural Subnetwork
 ↓
Perturbation
 ↓
Propagation
 ↓
Circuit State

Primary tools:

NetworkX

NumPy

SciPy

Custom simulation engine

---

## 8.3 Behavioral Scale

The behavioral layer handles:

Circuit State
 ↓
Network Metrics
 ↓
Behavioral Proxy

Potential behavioral proxies:

- Locomotion
- Activity
- Avoidance
- Exploration
- Sensory response
- Motor output

These are computational behavioral proxies, not automatically observed animal behaviors.

---

# 9. DEVELOPMENT STRATEGY

The project must be built vertically.

Do NOT build the entire backend first.

Do NOT build the entire frontend first.

Do NOT implement chemistry before the connectome architecture works.

Do NOT implement behavioral prediction before the neural simulation works.

Each phase should produce a functioning component that can be tested independently.

---

# 10. DEVELOPMENT ROADMAP

The official development order is:

PHASE 0
Project Foundation

↓

PHASE 1
Synthetic Connectome Engine

↓

PHASE 2
3D Synthetic Connectome Visualization

↓

PHASE 3
Real Drosophila Connectome Provider

↓

PHASE 4
Real Connectome Visualization

↓

PHASE 5
Neural Perturbation Engine

↓

PHASE 6
Network Analysis

↓

PHASE 7
Chemical Engine

↓

PHASE 8
Target & Evidence Engine

↓

PHASE 9
Drosophila Biological Mapping

↓

PHASE 10
Exposure / Effect Model

↓

PHASE 11
Optional Molecular Docking

↓

PHASE 12
Optional Molecular Dynamics

↓

PHASE 13
Behavior Engine

↓

PHASE 14
Validation Engine

↓

PHASE 15
Multi-Compound Formulations

This order is intentional.

Do not skip ahead unless explicitly instructed.

---

# 11. PHASE 0 — PROJECT FOUNDATION

## Goal

Create the basic application foundation.

Backend:

Python 3.11+

FastAPI

Pydantic

Frontend:

React

TypeScript

Vite

Create:

- Backend application
- Frontend application
- Basic API
- Basic frontend shell
- Development configuration
- Testing configuration
- `.gitignore`
- `pyproject.toml`
- `package.json`

Implement:

GET /health

Expected:

{
    "status": "ok"
}

Frontend should be able to communicate with the backend.

## Acceptance Criteria

- Backend starts.
- Frontend starts.
- `/health` works.
- Frontend can call backend.
- No major console errors.
- Basic tests pass.

DO NOT implement:

- Real connectome
- Chemistry
- Docking
- Neural simulation
- Behavioral modeling

---

# 12. PHASE 1 — SYNTHETIC CONNECTOME ENGINE

## Goal

Create the graph architecture using synthetic data.

This phase exists to validate the software architecture before using real biological data.

Create:

ConnectomeProvider

and:

SyntheticConnectomeProvider

Synthetic neurons should contain:

- neuron_id
- cell_type
- region
- x
- y
- z

Connections should contain:

- source_neuron
- target_neuron
- weight

The graph must support deterministic generation using a random seed.

Required operations:

- Get neuron
- Get neurons by cell type
- Get neurons by region
- Get neighbors
- Get connections
- Extract subgraph

## Acceptance Criteria

- Synthetic graph generates.
- Graph queries work.
- Neurons can be selected.
- Connections can be retrieved.
- Subgraphs can be extracted.
- Tests pass.

---

# 13. PHASE 2 — 3D SYNTHETIC CONNECTOME

## Goal

Visualize the synthetic graph.

Use:

Three.js

React Three Fiber

Drei

The user must be able to:

- Rotate
- Zoom
- Pan
- Select neurons
- View neuron metadata
- Highlight connected neurons
- Highlight connections

Visualization:

Neuron = 3D point/sphere

Connection = line/curve

Selected neuron = highlighted

Connected neurons = highlighted

## Acceptance Criteria

The synthetic connectome is interactively explorable in 3D.

Do not implement real biological data yet.

---

# 14. PHASE 3 — REAL CONNECTOME PROVIDER

## Goal

Introduce the actual Drosophila connectome.

Create:

GoogleJaneliaConnectomeProvider

IMPORTANT:

Before implementing the provider:

1. Verify the current official data source.
2. Verify dataset version.
3. Verify access method.
4. Verify license.
5. Verify available metadata.
6. Verify available connectivity information.
7. Document the source.
8. Avoid downloading unnecessarily large datasets.

Do not invent API endpoints.

Do not assume undocumented formats.

The provider must implement the same interface as:

SyntheticConnectomeProvider.

Architecture:

ConnectomeProvider
       ↑
       ├── SyntheticConnectomeProvider
       │
       └── GoogleJaneliaConnectomeProvider

The rest of the application must not depend directly on the specific provider.

---

# 15. PHASE 4 — REAL CONNECTOME VISUALIZATION

## Goal

Render real connectome-derived subnetworks.

The system should support:

- Neuron search
- Brain-region filtering
- Neuron selection
- Metadata display
- Upstream connections
- Downstream connections
- N-hop expansion
- Subgraph visualization

IMPORTANT:

Do NOT load the complete connectome into browser memory.

Use:

Full Dataset
 ↓
Server-side Query
 ↓
Relevant Subgraph
 ↓
Frontend

---

# 16. PHASE 5 — NEURAL PERTURBATION ENGINE

## Goal

Introduce computational neural perturbation.

Initial supported perturbations:

1. Node activation
2. Node suppression
3. Edge-weight modification

Example:

Neuron A:

baseline = 1.0

Perturbation:

activity = 0.0

Then propagate the effect through the network.

Start with an interpretable graph-based model.

Do NOT immediately implement highly complex biological neuron dynamics.

Potential initial abstraction:

activity_next =
activation_function(
    weighted_sum_of_incoming_activity
)

The mathematical implementation must be documented when this phase is reached.

---

# 17. PHASE 6 — NETWORK ANALYSIS

Calculate:

- Number of affected neurons
- Propagation depth
- Degree
- Weighted degree
- Betweenness centrality
- Closeness centrality
- PageRank where appropriate
- Network density
- Community/module structure
- Upstream affected neurons
- Downstream affected neurons

Network analysis must operate on the simulation graph.

---

# 18. PHASE 7 — CHEMICAL ENGINE

## Goal

Allow arbitrary chemical compounds to enter the system.

Input:

- Compound name
- SMILES
- Optional identifier
- Concentration
- Unit
- Exposure duration
- Exposure route

Use RDKit.

Calculate:

- Molecular weight
- LogP
- TPSA
- H-bond donors
- H-bond acceptors
- Rotatable bonds
- Ring count
- Molecular formula
- Canonical SMILES
- Molecular fingerprint

Invalid structures must produce structured errors.

The chemical system must remain independent from the neural simulation engine.

---

# 19. PHASE 8 — TARGET & EVIDENCE ENGINE

Map compounds to biological targets.

Evidence must be categorized.

Examples:

EXPERIMENTAL

CURATED_DATABASE

LITERATURE_INFERENCE

COMPUTATIONAL

MODEL_ASSUMPTION

Do NOT treat computational predictions as confirmed experimental targets.

Every target relationship should retain provenance where possible.

Example:

{
    "target": "TARGET_ID",
    "organism": "Drosophila melanogaster",
    "evidence_type": "experimental",
    "source": "SOURCE",
    "source_id": "ID",
    "confidence": "high"
}

---

# 20. PHASE 9 — DROSOPHILA BIOLOGICAL MAPPING

Conceptual pipeline:

Compound
 ↓
Molecular Target
 ↓
Drosophila Protein / Receptor
 ↓
Relevant Cell Type
 ↓
Relevant Neuron
 ↓
Connectome

This layer must remain separate from the connectome provider.

Do not hard-code biological relationships into simulation code.

---

# 21. PHASE 10 — EXPOSURE / EFFECT MODEL

IMPORTANT:

Do NOT assume:

Concentration
 ↓
Neural Activity

Instead:

Concentration
 ↓
Exposure
 ↓
Target Effect
 ↓
Neural Perturbation
 ↓
Network Propagation

Where supported, an effect model may use a Hill-type relationship:

E(C) =
Emax × C^n /
(EC50^n + C^n)

Where:

C = concentration

Emax = maximum effect

EC50 = half-maximal effective concentration

n = Hill coefficient

Only use experimentally supported parameters when available.

If parameters are unavailable:

- Allow user input.
- Use explicit assumptions.
- Label results as model-derived.

Never silently invent biological parameters.

---

# 22. PHASE 11 — MOLECULAR DOCKING

Docking is OPTIONAL.

Docking should be treated as computational evidence / hypothesis generation.

Pipeline:

Compound
 ↓
Target Protein
 ↓
Protein Preparation
 ↓
Ligand Preparation
 ↓
Docking
 ↓
Binding Pose
 ↓
Interaction Analysis

Potential outputs:

- Docking score
- Binding pose
- Interacting residues
- Hydrogen bonds
- Hydrophobic interactions

IMPORTANT:

Docking score is NOT experimental potency.

Never convert docking score directly into biological confirmation.

---

# 23. PHASE 12 — MOLECULAR DYNAMICS

Molecular dynamics is OPTIONAL.

It must NOT be part of the main interactive simulation loop.

Use MD only for selected compound-target systems when deeper molecular validation is justified.

Potential outputs:

- RMSD
- RMSF
- Hydrogen-bond persistence
- Interaction stability

MD is a secondary validation layer.

Do not make it a V1 requirement.

---

# 24. PHASE 13 — BEHAVIOR ENGINE

The behavior engine receives circuit/network outputs.

Potential behavioral proxies:

- Locomotion
- Activity
- Avoidance
- Exploration
- Sensory response
- Motor output

IMPORTANT:

These are computational proxies.

Do not state:

"The fly will stop moving."

Instead:

"The simulation predicts suppression of locomotion-associated circuit activity."

The distinction between simulation and experimental observation must always be preserved.

---

# 25. PHASE 14 — VALIDATION ENGINE

Compare computational results with published experimental observations.

Possible comparisons:

- Direction of effect
- Circuit involvement
- Behavioral phenotype
- Network response
- Literature evidence

The system must support disagreement.

Do not force simulations to match literature.

Possible result:

MODEL / EXPERIMENT AGREEMENT

or:

MODEL / EXPERIMENT DISCREPANCY

---

# 26. PHASE 15 — MULTI-COMPOUND FORMULATIONS

The platform must support multiple compounds.

Example:

FORMULATION A

Compound A:
2 mg/L

Compound B:
0.5 mg/L

Compound C:
0.1 mg/L

Exposure:

24 hours

Each compound must remain individually represented through:

Chemical analysis
 ↓
Target mapping
 ↓
Effect model

Effects can then be combined at the perturbation/network level.

Do not automatically call interactions:

"synergy"

or

"antagonism"

unless a formal model and evidence support those terms.

Use:

"predicted interaction effect"

when appropriate.

---

# 27. FORMULATION MODEL

Example:

{
    "formulation_id": "FORM001",

    "components": [
        {
            "compound_id": "CHEM001",
            "concentration": 2.0,
            "unit": "mg/L"
        }
    ],

    "exposure": {
        "duration": 24,
        "duration_unit": "hours",
        "route": "contact"
    }
}

The formulation model should eventually support:

- Multiple compounds
- Concentration
- Dose
- Percentage
- Exposure duration
- Exposure route
- Environmental parameters

---

# 28. CONNECTOME PROVIDER CONTRACT

Use this abstraction:

```python
class ConnectomeProvider:

    def get_neuron(self, neuron_id):
        ...

    def get_neurons_by_cell_type(self, cell_type):
        ...

    def get_neurons_by_region(self, region):
        ...

    def get_neighbors(self, neuron_id, hops=1):
        ...

    def get_connections(self, neuron_id):
        ...

    def extract_subgraph(self, neuron_ids):
        ...
        29. SIMULATION ENGINE CONTRACT

Use:

class SimulationEngine:

    def initialize(self, graph, perturbations):
        ...

    def step(self, dt):
        ...

    def run(self, duration):
        ...

    def get_state(self):
        ...

    def get_metrics(self):
        ...

The simulation model should be replaceable.

Do not tightly couple the simulation engine to the frontend.

30. REPOSITORY ARCHITECTURE

The intended repository structure is:

Drosophila-NeuroAtlas/

├── README.md
├── AGENTS.md
├── LICENSE
├── pyproject.toml
├── .gitignore
│
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ │
│ │ ├── api/
│ │ ├── models/
│ │ ├── chemistry/
│ │ ├── targets/
│ │ ├── docking/
│ │ ├── connectome/
│ │ ├── simulation/
│ │ ├── network/
│ │ ├── behavior/
│ │ └── validation/
│ │
│ └── tests/
│
├── frontend/
│ └── src/
│ ├── components/
│ ├── views/
│ ├── scene/
│ ├── formulation/
│ ├── simulation/
│ ├── charts/
│ └── api/
│
├── data/
│ ├── raw/
│ ├── processed/
│ ├── metadata/
│ ├── synthetic/
│ └── literature/
│
├── simulations/
│ ├── experiments/
│ └── results/
│
├── notebooks/
│ ├── connectome_exploration/
│ ├── molecular_analysis/
│ ├── network_analysis/
│ └── validation/
│
├── docs/
│ ├── scientific_model.md
│ ├── connectome.md
│ ├── molecular_layer.md
│ ├── simulation.md
│ ├── validation.md
│ └── data_sources.md
│
└── scripts/
├── download_data.py
├── preprocess_connectome.py
└── build_subgraph.py

IMPORTANT:

Do not create every directory or file immediately.

Create files when required by the current implementation phase.

Avoid empty placeholder modules unless they are required for architecture or imports.

31. FRONTEND ARCHITECTURE

The eventual frontend should contain:

Fly View

A high-level representation of the Drosophila model.

Brain View

3D brain/circuit visualization.

Connectome View

Neuron and synaptic network exploration.

Formulation View

Chemical/formulation configuration.

Simulation View

Perturbation and simulation controls.

Results View

Network metrics and behavioral proxies.

Use:

React

TypeScript

Three.js

React Three Fiber

Drei

32. PERFORMANCE RULES

The complete connectome must NOT be rendered in the browser by default.

Use:

FULL DATASET
↓
INDEX / QUERY
↓
RELEVANT SUBGRAPH
↓
BROWSER

Use:

Lazy loading
Server-side filtering
Subgraph extraction
Caching
Spatial filtering
Level-of-detail rendering
WebGL

Do not optimize prematurely.

First make the small subgraph work correctly.

33. DATA STORAGE

Potential storage architecture:

Raw scientific data:

Parquet / HDF5

Metadata:

JSON

Application metadata:

SQLite

Experiments:

SQLite / structured JSON

Large graph data should not be unnecessarily stored as giant JSON files.

34. API ARCHITECTURE

Potential endpoints:

GET /health

POST /compounds

GET /compounds/{compound_id}

POST /formulations

GET /formulations/{formulation_id}

GET /connectome/neuron/{neuron_id}

GET /connectome/neuron/{neuron_id}/neighbors

POST /connectome/subgraph

POST /simulations

GET /simulations/{simulation_id}

GET /simulations/{simulation_id}/network

GET /simulations/{simulation_id}/behavior

IMPORTANT:

Do not implement all endpoints at once.

Implement endpoints only when required by the current phase.

35. ERROR HANDLING

Use structured errors.

Example:

{
"error": {
"code": "INVALID_SMILES",
"message": "The provided SMILES could not be parsed."
}
}

Do not expose raw Python stack traces to users.

Technical details should be logged server-side.

36. TESTING RULES

Every major module requires tests.

At minimum:

Unit tests
Integration tests
API tests
Frontend component tests
Simulation reproducibility tests

Deterministic behavior should be tested.

Given:

same graph
+
same parameters
+
same perturbation
+
same random seed

the simulation should produce the same result.

37. PROVENANCE

Every external dataset must record:

Source
Dataset name
Version
Access date
License
Citation
Processing steps

Every biological relationship should retain evidence information where possible.

Never invent provenance.

Never fabricate literature.

Never invent database identifiers.

38. SCIENTIFIC BOUNDARIES

Always distinguish:

EXPERIMENTAL EVIDENCE

from

COMPUTATIONAL EVIDENCE

from

MODEL ASSUMPTION

from

SYNTHETIC TEST DATA.

For example:

Docking score
≠
Experimental binding affinity

Target prediction
≠
Confirmed biological target

Network perturbation
≠
Observed neural activity

Behavioral proxy
≠
Observed animal behavior

39. INITIAL VALIDATION COMPOUND

The initial validation compound is:

IMIDACLOPRID

It is being used because it provides a practical initial case for connecting:

Chemical structure
↓
Known biological targets
↓
Drosophila evidence
↓
Neural effects
↓
Behavioral observations

IMPORTANT:

Do NOT hard-code imidacloprid-specific logic into the architecture.

The platform must remain compound-agnostic.

40. INITIAL END-TO-END EXPERIMENT

The first meaningful complete experiment should eventually look like:

IMIDACLOPRID
↓
SMILES
↓
RDKit Molecular Profile
↓
Target Evidence
↓
Drosophila Biological Mapping
↓
Relevant Neurons
↓
Real Connectome Subnetwork
↓
Computational Perturbation
↓
Network Propagation
↓
Circuit Response
↓
Behavioral Proxy
↓
Experimental/Literature Comparison
↓
Interactive 3D Visualization

This is the first major scientific demonstration.

41. MULTI-COMPOUND FUTURE

Eventually support:

Compound A
Compound B
Compound C
↓
FORMULATION
↓
Individual target mappings
↓
Individual effect models
↓
Combined network perturbation
↓
Network interaction analysis
↓
Behavioral proxies

Do not make multi-compound modeling part of the initial implementation.

42. OPTIONAL FUTURE EXTENSIONS

After the core system works, potential extensions include:

Dose-response sweeps
Multiple compounds
Compound interaction analysis
Additional behavioral circuits
Sex-specific datasets
Additional Drosophila datasets
Population-level modeling
Ecological exposure scenarios
Cross-species comparisons
More advanced neuron models
Molecular dynamics
Machine learning where scientifically justified

These are NOT V1 requirements.

43. CODE QUALITY RULES

Prefer:

Small modules
Clear interfaces
Type hints
Pydantic models
Descriptive names
Testable functions
Explicit dependencies
Minimal coupling

Avoid:

Giant files
Giant classes
Global state
Hard-coded biological mappings
Hard-coded chemical results
Hidden assumptions
Unnecessary dependencies
Duplicate implementations
44. DEPENDENCY RULE

Do not install a dependency simply because it might be useful later.

Only add dependencies required by the current task.

Before adding a major dependency:

Check whether an existing dependency already solves the problem.
Check whether the dependency is maintained.
Check compatibility.
Keep the architecture modular.
45. NO PREMATURE OPTIMIZATION

Do not optimize the complete connectome before a small graph works.

Do not implement distributed computing before local execution becomes a bottleneck.

Do not implement GPU simulation before the CPU model is validated.

Do not implement advanced neural dynamics before the graph architecture works.

Correctness comes before scale.

46. AGENT DECISION PROCESS

Whenever the user gives a new task:

STEP 1

Read this file.

STEP 2

Inspect the repository.

STEP 3

Identify the current implementation state.

STEP 4

Map the user request to the appropriate phase.

STEP 5

Check whether dependencies are complete.

STEP 6

Implement only the requested work.

STEP 7

Run tests.

STEP 8

Fix errors.

STEP 9

Verify existing functionality.

STEP 10

Report:

What changed
Files created/modified
Tests run
Results
Any limitations
What the next phase would be

STEP 11

STOP.

47. IF THE USER GIVES AN AMBIGUOUS REQUEST

Do not make large architectural assumptions.

Inspect:

Current phase
Existing code
This file
User's requested scope

If the request can safely be interpreted from context, proceed.

If an important scientific or architectural decision is genuinely ambiguous, ask before implementing it.

Do not invent requirements.

48. IF EXISTING CODE IS BROKEN

Do not immediately rewrite the entire project.

First:

Identify the failure.
Identify the affected module.
Determine whether the problem is local or architectural.
Fix the smallest necessary component.
Run tests.
Verify regression behavior.

Preserve working code.

49. IF A FUTURE FEATURE IS REQUIRED FOR THE CURRENT PHASE

Implement the smallest interface necessary.

Example:

If Phase 1 needs a future-compatible provider:

Create the interface.

Do NOT implement the entire real connectome provider.

Example:

If simulation architecture needs a future behavioral interface:

Create the abstraction.

Do NOT build the complete behavior engine.

50. DEFINITION OF DONE

A task is complete only when:

Requested functionality exists.
Existing functionality still works.
Tests pass.
No obvious runtime errors remain.
The implementation follows this architecture.
Scientific assumptions are explicit.
No future phase was unnecessarily implemented.
51. PHASE COMPLETION RULE

At the end of every phase:

Run all relevant tests.
Start the relevant application/services.
Verify the feature manually where applicable.
Fix discovered problems.
Update the current project status in this file only if appropriate.
Report the completed phase.
STOP.

Do NOT automatically start the next phase.

52. FIRST DEVELOPMENT TASK

When the user first instructs the agent to begin development:

Read this file.

Inspect the repository.

Determine whether the project is empty/new.

If it is a new repository:

Begin with PHASE 0 only.

Do not implement the connectome yet.

Do not implement chemistry yet.

Do not implement simulation yet.

Do not implement docking yet.

Do not implement behavioral modeling yet.

Create only the foundation required for Phase 0.

53. FIRST USER COMMAND

The recommended first command is:

Read AGENTS.md completely.

Inspect the current repository.

This is a new Drosophila-NeuroAtlas project.

Start PHASE 0 only.

Build the project foundation described in AGENTS.md.

Do not implement any future phase.

After implementation, run the tests, verify the backend and frontend, report exactly what was completed, and stop.

54. SUBSEQUENT USER COMMANDS

After Phase 0:

Read AGENTS.md. Phase 0 is complete. Start Phase 1 only. Inspect the existing implementation first. Do not implement Phase 2 or later.

After Phase 1:

Read AGENTS.md. Phase 1 is complete. Start Phase 2 only. Preserve the existing implementation and do not implement future phases.

After Phase 2:

Read AGENTS.md. Phase 2 is complete. Start Phase 3 only. Before implementing the real connectome provider, verify the current official Google/Janelia data source and document the exact access method.

Continue this pattern for every phase.

55. GOLDEN RULE

The entire project should evolve in this order:

WORKING FOUNDATION
↓
WORKING GRAPH
↓
WORKING 3D VISUALIZATION
↓
REAL CONNECTOME
↓
PERTURBATION ENGINE
↓
NETWORK ANALYSIS
↓
CHEMICAL MAPPING
↓
BIOLOGICAL MAPPING
↓
EFFECT MODEL
↓
BEHAVIORAL PROXIES
↓
VALIDATION
↓
MULTI-COMPOUND FORMULATIONS

Never build the final interface around functionality that does not exist.

Never fake scientific functionality to make a demo appear complete.

56. FINAL V1 DEFINITION

V1 should eventually demonstrate:

A real Drosophila connectome-derived neural subnetwork can be loaded, explored in 3D, computationally perturbed, simulated using an interpretable graph-based model, analyzed using network metrics, and connected to a molecular perturbation with explicit evidence and assumptions.

The system should clearly distinguish:

REAL DATA

COMPUTATIONAL RESULTS

MODEL ASSUMPTIONS

SYNTHETIC TEST DATA

This is the minimum scientifically meaningful version of Drosophila-NeuroAtlas.

Everything beyond this is an extension.

END OF AGENT MASTER SPECIFICATION

### Then your workflow becomes very simple

Put **only this one file** in the repo:

```text
AGENTS.md

Then tell Antigravity:

Read AGENTS.md completely. Inspect the repository. Start Phase 0 only.

When Phase 0 is done:

Read AGENTS.md. Phase 0 is complete. Start Phase 1 only.

Then:

Phase 1 is complete. Start Phase 2 only.

And so on.

This is much better for what you're trying to do than ARCHITECTURE.md, because AGENTS.md acts as the persistent instruction layer while your individual prompts act as the current task assignment.