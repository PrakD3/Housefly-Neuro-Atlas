# Phase 5 — Neural Perturbation Engine Specification

> **CRITICAL SCIENTIFIC DISCLAIMER**
>
> This simulation engine is a **computational network model** operating on graph-level normalized states.
> **It does not reproduce experimentally measured neuronal electrophysiology, membrane potentials, or biological action potential dynamics.**
> Normalized activity values $a \in [0, 1]$ are computational state variables, not firing rates in Hertz.

---

## 1. Mathematical Formulation

The neural perturbation engine operates on a directed graph $G = (V, E)$, derived from either the synthetic connectome or a bounded real *Drosophila melanogaster* connectome subgraph (HHMI Janelia MaleCNS v1.0).

### 1.1 State Variables
- Each neuron $j \in V$ is associated with a normalized computational state variable:
  $$a_t[j] \in [0.0, 1.0]$$
  where:
  - $0.0$ = minimal modeled activity / inactive state
  - $1.0$ = maximal modeled activity within the simulation framework
  - Initial resting baseline: $a_0[j] = a_{\text{baseline}}$ (default $0.2$)

### 1.2 Edge Normalization
For each directed synaptic connection $(i, j) \in E$ with source neuron $i$ and target neuron $j$:
- If connection weight $w_{ij} > 0$ is provided, it is retained.
- If connection weight is missing, non-positive, or NaN, a computational fallback weight $w_{ij} = 1.0$ is assigned and explicitly flagged (`is_fallback = True`).
- Incoming edge weights are normalized per target neuron $j$:
  $$\tilde{w}_{ij} = \frac{w_{ij}}{\sum_{k \in \text{pre}(j)} w_{kj}}$$
  ensuring $\sum_{i \in \text{pre}(j)} \tilde{w}_{ij} = 1.0$ whenever $\text{pre}(j) \neq \emptyset$.

### 1.3 Discrete-Time Propagation
At each discrete timestep $k$ with step size $\Delta t$:

1. **Calculate Network Propagation:**
   For each neuron $j \in V$, the propagated input from upstream presynaptic neurons is:
   $$I_k[j] = \text{propagation\_strength} \cdot \sum_{i \in \text{pre}(j)} \tilde{w}_{ij} \cdot \left(a_k[i] - a_{\text{baseline}}\right)$$
   Passive decay towards the resting baseline combined with propagated input yields the intermediate state:
   $$\tilde{a}_{k+1}[j] = a_{\text{baseline}} + \text{decay} \cdot \left(a_k[j] - a_{\text{baseline}}\right) + I_k[j]$$

2. **Apply Active Perturbations:**
   A perturbation $P$ is active at time $t$ if $\text{start\_time} \le t < \text{start\_time} + \text{duration}$.
   For each target neuron $j \in \text{targets}(P)$:
   - **Activation / Excitation** (positive modeled shift):
     $$\tilde{a}_{k+1}[j] \leftarrow \tilde{a}_{k+1}[j] + \text{magnitude}$$
   - **Inhibition / Suppression** (negative modeled shift):
     $$\tilde{a}_{k+1}[j] \leftarrow \tilde{a}_{k+1}[j] - \text{magnitude}$$
   - **Edge Weight Modification**:
     Outgoing transmission weights for the target neuron are scaled by $(1 - \text{magnitude})$.

3. **Clamp Activity to Bounds:**
   $$a_{k+1}[j] = \max\left(a_{\min}, \min\left(a_{\max}, \tilde{a}_{k+1}[j]\right)\right)$$
   where $a_{\min} = 0.0$ and $a_{\max} = 1.0$.

4. **Record State & Advance Time:**
   $$t_{k+1} = t_k + \Delta t$$

---

## 2. Baseline vs. Perturbed Comparison

To rigorously isolate the computational impact of any perturbation, the engine runs two paired trajectories under identical initial conditions and network topologies:

1. **Baseline Simulation**: Perturbations = `[]` (unperturbed control trajectory).
2. **Perturbed Simulation**: Evaluates active perturbations.

For each neuron $j \in V$ at any time point $t$:
$$\Delta a_t[j] = a_{t, \text{perturbed}}[j] - a_{t, \text{baseline}}[j]$$

- $\Delta a > 0$: Net computational activation relative to baseline.
- $\Delta a < 0$: Net computational suppression relative to baseline.
- $\Delta a = 0$: Unaffected node.

---

## 3. Computational Equivalence of Perturbation Types

| Perturbation Effect | Mathematical Formulation | Computational Meaning | Biological Note |
|---|---|---|---|
| `activation` | $+ \text{magnitude}$ | Positive shift in target activity | Computational model parameter; does not imply specific ligand efficacy. |
| `excitation` | $+ \text{magnitude}$ | Identical to `activation` | Equivalent in this graph model. |
| `inhibition` | $- \text{magnitude}$ | Negative shift in target activity | Dimensionless model parameter; does not represent binding affinity. |
| `suppression` | $- \text{magnitude}$ | Identical to `inhibition` | Equivalent in this graph model. |
| `edge_weight_modification` | Scale $w_{ij}$ by $(1 - M)$ | Attenuation of synaptic transmission | Models connection impairment without modifying target firing. |

---

## 4. Multi-Hop Propagation Tracking

For each neuron $j \in V$, the directed hop distance $h(j)$ is computed via Dijkstra / BFS shortest paths from all active perturbation targets:
$$h(j) = \min_{t \in \text{targets}} \text{dist}_G(t, j)$$

The engine records:
- **First Time of Change**: The earliest simulation time $t$ where $|\Delta a_t[j]| > 0.01$.
- **Peak Activity Change**: The final/maximal activity deviation $\Delta a$.
- **Hop Distance**: The topological graph distance from the perturbation site.

---

## 5. Network Metrics

Metrics summarize computational network state and are strictly **network-level**, not behavioral:

- **Mean Activity**: $\frac{1}{|V|} \sum_{j \in V} a[j]$
- **Active Neuron Count**: Count of neurons where $a[j] > a_{\text{baseline}} + 0.05$
- **Max / Min Activity**: $\max_{j} a[j]$, $\min_{j} a[j]$
- **Total Network Activity**: $\sum_{j \in V} a[j]$
- **Downstream Affected Count**: Number of non-target neurons with $|\Delta a[j]| > 0.01$

---

## 6. Engineering Safety Limits

To guarantee server stability and browser responsiveness:
- **Max Simulation Neurons**: 500 neurons per simulation run.
- **Max Perturbations**: 20 perturbations per request.
- **Max Duration**: 50.0 seconds.
- **Max Timesteps**: 1000 steps ($duration / dt \le 1000$).
- **Bounded Result Cache**: In-memory LRU cache stores up to 50 recent simulation results.

---

## 7. Provenance & Reproducibility

Every `SimulationResult` encapsulates a comprehensive `SimulationProvenance` record:
- Unique simulation ID (`sim_<uuid>`)
- Connectome provider (`synthetic` or `real`)
- Dataset name (`synthetic` or `cns`)
- Dataset version (e.g. `v1.0` for MaleCNS)
- Is-synthetic flag
- Creation timestamp (UTC ISO-8601)
- Model version (`0.1.0-phase5`)
- Full simulation configuration and perturbation definitions

Given identical graph inputs, configuration, and perturbations, the discrete simulation produces **bit-identical deterministic outputs**.
