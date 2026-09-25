# Scientific Model Specification — Drosophila-NeuroAtlas

## 1. Multiscale Architecture Overview

Drosophila-NeuroAtlas investigates how chemical perturbations propagate through real connectomic neural networks. The architecture bridges three distinct computational scales:

```
[MOLECULAR SCALE]           (Phases 7–12: RDKit, Target Mapping, Docking)
       ↓
[NEURAL NETWORK SCALE]      (Phases 1–6: Connectome, Perturbation, Propagation)
       ↓
[BEHAVIORAL SCALE]          (Phase 13: Circuit state to computational behavioral proxies)
```

**Phase 5 establishes the Neural Network Scale perturbation engine.** It provides an explicit mathematical framework to receive targets and propagate normalized state shifts across connectome subgraphs.

---

## 2. Core Scientific Principles

### 2.1 Explicit Assumptions Over Biological Fabrication
- When biological parameters (such as biophysical channel kinetics or membrane capacitances) are unmeasured or absent from connectomic datasets, **they must never be fabricated**.
- A simple, interpretable, deterministic graph-level propagation model is preferred over an uncalibrated biophysical simulation that falsely implies biological precision.

### 2.2 Distinctions and Boundaries
The following distinctions are fundamental to this platform:

| Concept | What It Is (Computational Model) | What It Is NOT (Biological Truth) |
|---|---|---|
| **Normalized Activity ($a \in [0, 1]$)** | Dimensionless computational state variable representing relative activation | Firing rate in Hertz or intracellular membrane potential in millivolts |
| **Edge Weight ($w_{ij}$)** | Observed synaptic contact count or normalized transmission weight | Dynamic neurotransmitter release probability or quantal EPSP amplitude |
| **Perturbation Magnitude ($M$)** | Dimensionless shift applied to model activity | Agonist/antagonist concentration, $K_d$, $IC_{50}$, or percentage inhibition |
| **Graph Propagation** | Discrete-time linear-decay diffusion across directed graph edges | Action potential propagation or synaptic facilitation/depression |
| **Baseline Comparison ($\Delta a$)** | Difference between perturbed and unperturbed model trajectories | Experimentally observed neurotoxic symptom |

---

## 3. Explicit Model Assumptions

In Phase 5, the following computational assumptions are explicitly made:

1. **Resting Baseline Homogeneity**: In the absence of external perturbations or presynaptic drive, all neurons in a subgraph are assumed to share a default resting state ($a_{\text{baseline}} = 0.2$).
2. **In-Degree Normalization**: Synaptic influence on a postsynaptic neuron is normalized by the total sum of its incoming edge weights, preventing high-in-degree nodes from exploding numerically.
3. **Fallback Connection Weight**: If a connectomic connection lacks a positive numeric weight, a computational fallback weight of $1.0$ is assigned and explicitly flagged (`is_fallback = True`).
4. **Directional Flow**: Perturbations propagate strictly along directed chemical synaptic connections (source $\rightarrow$ target).
5. **Computational Equivalence**: Activation and Excitation are modeled identically (positive activity shift); Inhibition and Suppression are modeled identically (negative activity shift).

---

## 4. Software Verification vs Biological Truth

Mathematical sanity tests implemented for Phase 5 verify that the software correctly follows its mathematical rules:
- **Baseline Invariance**: With zero perturbation, the network preserves its baseline trajectory identically ($\Delta a = 0$).
- **State Bounding**: Modeled activity is strictly clamped to $[0.0, 1.0]$.
- **Directional Response**: Positive perturbations strictly increase target activity; inhibitory perturbations strictly decrease target activity.
- **Topological Causality**: Zero propagation strength prevents all downstream propagation.
- **Monotonicity**: Increasing propagation strength monotonically increases the downstream activity deviation under sub-saturation conditions.

These tests validate the **software model**. They do **not** validate biological fact. Biological validation occurs in later validation phases (Phase 14).

---

## 5. Phase 6 — Network Analysis Framework

Phase 6 provides graph-theoretic and analytical quantification of the simulation results:
- **Structural Topology**: Graph density, directed in/out degree distributions, weakly/strongly connected components, and average shortest path lengths.
- **Topological Centrality**: Betweenness, in-degree, out-degree, and closeness centralities computed strictly on the directed graph. Centrality denotes graph positional properties, never biological criticality.
- **Dynamic Propagation Quantification**: Classifies model-affected neurons using an explicit computational threshold ($\theta$). Does not denote biological toxicity.
- **Target Reachability**: Explicit tracking of upstream partners and $k$-hop downstream reachability layers.

