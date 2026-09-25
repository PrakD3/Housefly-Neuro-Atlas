import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { 
  getConnectomeInfo, 
  getNeurons, 
  getNeuronNeighbors,
  getNeighborhood,
  Neuron, 
  Connection, 
  ConnectomeMetadata, 
  SubgraphResponse,
  SimulationResult,
  NetworkAnalysisResult,
} from '../../api/client';
import { Scene } from './Scene';
import { RealModePanel } from './RealModePanel';
import { ErrorPanel } from './ErrorPanel';
import { SimulationPanel } from './SimulationPanel';
import { NetworkAnalysisPanel } from './NetworkAnalysisPanel';
import { computeTransform, DEFAULT_SCENE_DIAMETER } from './VisualizationTransform';

export const ConnectomeViewer: React.FC = () => {
  const [metadata, setMetadata] = useState<ConnectomeMetadata | null>(null);
  const [neurons, setNeurons] = useState<Neuron[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [queryLoading, setQueryLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | undefined>(undefined);

  const [selectedNeuron, setSelectedNeuron] = useState<Neuron | null>(null);
  const [hoveredNeuron, setHoveredNeuron] = useState<Neuron | null>(null);
  const [neighborsData, setNeighborsData] = useState<SubgraphResponse | null>(null);
  const [showConnections, setShowConnections] = useState<boolean>(true);
  const [wasTruncated, setWasTruncated] = useState<boolean>(false);
  const [activeFocalId, setActiveFocalId] = useState<string | null>(null);

  // Phase 5 & 6: Simulation and Analysis state
  const [activeRightTab, setActiveRightTab] = useState<'inspector' | 'simulation' | 'analysis'>('inspector');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [simulationMode, setSimulationMode] = useState<'none' | 'perturbed' | 'baseline' | 'delta'>('none');
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [networkAnalysis, setNetworkAnalysis] = useState<NetworkAnalysisResult | null>(null);
  const [highlightAffectedOnly, setHighlightAffectedOnly] = useState<boolean>(false);
  const [activeHopFilter, setActiveHopFilter] = useState<number | 'all'>('all');

  // Filters (used in synthetic mode)
  const [searchQuery, setSearchQuery] = useState("");
  const [cellTypeFilter, setCellTypeFilter] = useState("All");
  const [regionFilter, setRegionFilter] = useState("All");

  const [canvasKey, setCanvasKey] = useState<number>(0);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setErrorStatus(undefined);
      const info = await getConnectomeInfo();
      setMetadata(info);

      if (info.is_synthetic) {
        // Synthetic mode: load all neurons to allow full graph exploration
        const allNeurons = await getNeurons();
        setNeurons(allNeurons);
      } else {
        // Real mode: start empty to avoid loading 140,000+ neurons into browser memory
        setNeurons([]);
        setConnections([]);
      }
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to load connectome info');
      setErrorStatus(err.status || 500);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // When a neuron is selected in synthetic mode, fetch its 1-hop neighbors
  useEffect(() => {
    if (metadata?.is_synthetic && selectedNeuron) {
      const fetchNeighbors = async () => {
        try {
          const data = await getNeuronNeighbors(selectedNeuron.neuron_id, 1);
          setNeighborsData(data);
          setConnections(data.connections);
        } catch (err) {
          console.error("Failed to fetch neighbors", err);
        }
      };
      fetchNeighbors();
    } else if (metadata?.is_synthetic && !selectedNeuron) {
      setNeighborsData(null);
      setConnections([]);
    }
  }, [selectedNeuron, metadata?.is_synthetic]);

  // Load a neighborhood in real mode
  const handleLoadNeighborhood = useCallback(async (neuronId: string, hops: number = 1) => {
    try {
      setQueryLoading(true);
      setError(null);
      setErrorStatus(undefined);

      const data = await getNeighborhood(neuronId, hops);
      setNeurons(data.neurons);
      setConnections(data.connections);
      setNeighborsData(data);
      setWasTruncated(data.was_truncated);
      setActiveFocalId(neuronId);

      const central = data.neurons.find(n => n.neuron_id === neuronId) || data.neurons[0] || null;
      setSelectedNeuron(central);
      setCanvasKey(prev => prev + 1);
    } catch (err: any) {
      setError(err.message || `Failed to fetch neighborhood for neuron ${neuronId}`);
      setErrorStatus(err.status);
    } finally {
      setQueryLoading(false);
    }
  }, []);

  const handleClearRealMode = useCallback(() => {
    setNeurons([]);
    setConnections([]);
    setNeighborsData(null);
    setSelectedNeuron(null);
    setActiveFocalId(null);
    setWasTruncated(false);
    setError(null);
    setCanvasKey(prev => prev + 1);
  }, []);

  const handleSelectNeuron = useCallback((neuron: Neuron | null) => {
    setSelectedNeuron(prev => (prev?.neuron_id === neuron?.neuron_id ? null : neuron));
  }, []);

  const handleHoverNeuron = useCallback((neuron: Neuron | null) => {
    setHoveredNeuron(neuron);
  }, []);

  const toggleConnections = useCallback(() => {
    setShowConnections(prev => !prev);
  }, []);

  const resetCamera = useCallback(() => {
    setSelectedNeuron(null);
    setSearchQuery("");
    setCellTypeFilter("All");
    setRegionFilter("All");
    setCanvasKey(prev => prev + 1);
  }, []);

  // Timeline animation playback
  useEffect(() => {
    if (!isPlaying || !simulationResult) return;
    const interval = setInterval(() => {
      setCurrentStepIndex(prev => {
        if (prev >= simulationResult.time_series.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 150);
    return () => clearInterval(interval);
  }, [isPlaying, simulationResult]);

  const currentSimActivity = useMemo(() => {
    if (!simulationResult || simulationMode === 'none') return null;
    if (simulationMode === 'baseline') {
      return simulationResult.baseline_time_series[currentStepIndex]?.neuron_activity ?? null;
    }
    return simulationResult.time_series[currentStepIndex]?.neuron_activity ?? null;
  }, [simulationResult, simulationMode, currentStepIndex]);

  const currentSimDeltas = useMemo(() => {
    if (!simulationResult || simulationMode !== 'delta') return null;
    const map: Record<string, number> = {};
    for (const d of simulationResult.neuron_deltas) {
      map[d.neuron_id] = d.delta_activity;
    }
    return map;
  }, [simulationResult, simulationMode]);

  const targetNeuronIds = useMemo(() => {
    if (!simulationResult) return new Set<string>();
    const set = new Set<string>();
    for (const p of simulationResult.provenance.perturbations) {
      for (const t of p.target_neuron_ids) set.add(t);
    }
    return set;
  }, [simulationResult]);

  const affectedNeuronIds = useMemo(() => {
    if (!networkAnalysis) return new Set<string>();
    return new Set(
      networkAnalysis.perturbation_analysis.affected_neurons
        .filter(n => n.exceeds_threshold)
        .map(n => n.neuron_id)
    );
  }, [networkAnalysis]);

  const displayNeuron = hoveredNeuron || selectedNeuron;
  const isRealMode = metadata?.is_synthetic === false;

  // Calculate unique cell types and regions
  const cellTypes = useMemo(
    () => ["All", ...Array.from(new Set(neurons.map(n => n.cell_type))).sort()],
    [neurons]
  );
  const regions = useMemo(
    () => ["All", ...Array.from(new Set(neurons.map(n => n.region))).sort()],
    [neurons]
  );

  // Apply filters (only in synthetic mode)
  const filteredNeurons = useMemo(() => {
    if (isRealMode) {
      return neurons;
    }
    return neurons.filter(n => {
      if (searchQuery && !n.neuron_id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      if (cellTypeFilter !== "All" && n.cell_type !== cellTypeFilter) return false;
      if (regionFilter !== "All" && n.region !== regionFilter) return false;
      return true;
    });
  }, [neurons, searchQuery, cellTypeFilter, regionFilter, isRealMode]);

  // Normalization transform for real mode voxel coordinates
  const transform = useMemo(() => {
    if (!isRealMode || filteredNeurons.length === 0) {
      return null;
    }
    return computeTransform(filteredNeurons, DEFAULT_SCENE_DIAMETER);
  }, [isRealMode, filteredNeurons]);

  // Compute bounding box for camera framing
  const boundingBox = useMemo(() => {
    if (transform) {
      // In normalized real mode, scene coordinates are centered at [0, 0, 0]
      const size = transform.sceneSize;
      return {
        center: [0, 0, 0] as [number, number, number],
        width: size,
        height: size,
        depth: size,
        maxDimension: size,
      };
    }

    const spatialNeurons = filteredNeurons.filter(n => n.has_coordinates);
    if (spatialNeurons.length === 0) {
      return { center: [0, 0, 0] as [number, number, number], width: 40, height: 40, depth: 40, maxDimension: 40 };
    }
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;

    for (const n of spatialNeurons) {
      const x = n.x!;
      const y = n.y!;
      const z = n.z!;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }

    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const cz = (minZ + maxZ) / 2;
    const width = maxX - minX || 40;
    const height = Math.max(maxY - minY, 1) || 40;
    const depth = maxZ - minZ || 40;
    const maxDimension = Math.max(width, height, depth) || 40;

    return { center: [cx, cy, cz] as [number, number, number], width, height, depth, maxDimension };
  }, [filteredNeurons, transform]);

  if (loading) return <div className="loading-screen">Loading Connectome Data...</div>;

  // Color mapping for the legend
  const cellTypeColors: Record<string, string> = {
    "Sensory": "#fbbf24",     // yellow
    "Interneuron": "#a78bfa", // purple
    "Projection": "#f87171",  // red
    "Motor": "#34d399",       // green
    "Modulatory": "#38bdf8",  // cyan
    "descending": "#f97316",  // orange
    "ascending": "#a3e635",   // lime
    "visual": "#22d3ee",      // cyan
    "central": "#c084fc",     // lavender
  };

  return (
    <>
      <header className="app-header">
        <div className="header-title">
          <h1>Drosophila-NeuroAtlas</h1>
          <p className="subtitle">Connectome-driven computational neuroscience platform</p>
        </div>
        {/* Dynamic dataset badge — clearly distinguishes real from synthetic */}
        {metadata && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
            {metadata.is_synthetic ? (
              <>
                <div className="header-status" style={{color: '#fca5a5', border: '1px solid #7f1d1d'}}>
                  SYNTHETIC DATA
                </div>
                <p style={{fontSize: '0.7rem', color: '#94a3b8', margin: '4px 0 0 0', textTransform: 'uppercase', letterSpacing: '0.05em'}}>
                  Synthetic spatial layout — not anatomical coordinates
                </p>
              </>
            ) : (
              <>
                <div className="header-status" style={{color: '#86efac', border: '1px solid #14532d'}}>
                  REAL CONNECTOME
                </div>
                <p style={{fontSize: '0.7rem', color: '#86efac', margin: '4px 0 0 0', textTransform: 'uppercase', letterSpacing: '0.05em'}}>
                  {metadata.dataset_name} {metadata.dataset_version}
                </p>
              </>
            )}
          </div>
        )}
      </header>

      <main className="app-main">
        {/* LEFT PANEL */}
        <aside className="panel left-panel">
          <div>
            <h2 className="panel-title">Connectome</h2>
            <div className="data-row">
              <span className="data-label">Dataset</span>
              <span className="data-value">
                {metadata?.is_synthetic
                  ? 'Synthetic'
                  : metadata?.dataset_name ?? 'Real'}
              </span>
            </div>
            <div className="data-row">
              <span className="data-label">Version</span>
              <span className="data-value">
                {metadata?.is_synthetic
                  ? 'Dev / Test'
                  : metadata?.dataset_version ?? '—'}
              </span>
            </div>
            <div className="data-row">
              <span className="data-label">Status</span>
              <span className="data-value" style={{color: metadata?.is_synthetic ? '#fca5a5' : '#86efac'}}>
                {metadata?.is_synthetic ? 'Software Test Data' : 'Real Connectome Data'}
              </span>
            </div>
            {metadata?.organism && (
              <div className="data-row">
                <span className="data-label">Organism</span>
                <span className="data-value">{metadata.organism} {metadata.sex ? `(${metadata.sex})` : ''}</span>
              </div>
            )}
          </div>

          {/* Real Mode query panel vs Synthetic Mode filter controls */}
          {isRealMode ? (
            <RealModePanel
              onLoadNeighborhood={handleLoadNeighborhood}
              onClear={handleClearRealMode}
              isLoading={queryLoading}
              activeNeuronId={activeFocalId}
            />
          ) : (
            <div className="panel-section">
              <h2 className="panel-title">Controls</h2>
              
              <div className="control-group">
                <label>Search Neuron</label>
                <input 
                  type="text" 
                  placeholder="Neuron ID..." 
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
              </div>
              
              <div className="control-group">
                <label>Cell Type</label>
                <select value={cellTypeFilter} onChange={e => setCellTypeFilter(e.target.value)}>
                  {cellTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                </select>
              </div>
              
              <div className="control-group">
                <label>Region</label>
                <select value={regionFilter} onChange={e => setRegionFilter(e.target.value)}>
                  {regions.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
            </div>
          )}

          {/* Common display controls */}
          <div className="panel-section">
            <h2 className="panel-title">View Options</h2>
            <button className="btn btn-primary" style={{marginTop: '0.25rem', width: '100%'}} onClick={toggleConnections}>
              {showConnections ? "Hide Connections" : "Show Connections"}
            </button>
            <button className="btn" style={{marginTop: '0.5rem', width: '100%'}} onClick={resetCamera}>
              Reset View
            </button>
          </div>

          <div className="panel-section">
            <h2 className="panel-title">Legend</h2>
            <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem'}}>
              {Object.entries(cellTypeColors).map(([type, color]) => (
                <div key={type} style={{display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#cbd5e1'}}>
                  <div style={{width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color, boxShadow: `0 0 5px ${color}`}}></div>
                  <span>{type}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* CENTER VIEWPORT */}
        <section className="viewport" style={{ position: 'relative' }}>
          {error && (
            <ErrorPanel
              error={error}
              statusCode={errorStatus}
              onDismiss={() => setError(null)}
              onRetry={isRealMode && activeFocalId ? () => handleLoadNeighborhood(activeFocalId) : loadData}
            />
          )}

          {wasTruncated && (
            <div style={{
              position: 'absolute',
              top: '1rem',
              right: '1rem',
              zIndex: 10,
              backgroundColor: 'rgba(245, 158, 11, 0.9)',
              color: '#0f172a',
              padding: '0.4rem 0.8rem',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.02em',
            }}>
              Subgraph truncated to server limits (max 500 neurons)
            </div>
          )}

          {isRealMode && neurons.length === 0 && !queryLoading && !error && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: '#94a3b8',
              zIndex: 5,
              pointerEvents: 'none',
              maxWidth: '380px',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: 0.5 }}>⚡</div>
              <h3 style={{ color: '#e2e8f0', fontSize: '1rem', marginBottom: '0.5rem' }}>No Subgraph Loaded</h3>
              <p style={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                Enter a neuron body ID in the left panel to load and explore its subnetwork in 3D.
              </p>
            </div>
          )}

          <Canvas key={canvasKey}>
            <Scene
              neurons={filteredNeurons}
              connections={connections}
              neighborsData={neighborsData}
              selectedNeuron={selectedNeuron}
              showConnections={showConnections}
              onSelectNeuron={handleSelectNeuron}
              onHoverNeuron={handleHoverNeuron}
              center={boundingBox.center}
              width={boundingBox.width}
              height={boundingBox.height}
              depth={boundingBox.depth}
              transform={transform}
              simulationActivity={currentSimActivity}
              simulationDeltas={currentSimDeltas}
              simulationMode={simulationMode}
              targetNeuronIds={targetNeuronIds}
              affectedNeuronIds={affectedNeuronIds}
              highlightAffectedOnly={highlightAffectedOnly}
            />
          </Canvas>
          
          {displayNeuron && !selectedNeuron && (
            <div style={{
              position: 'absolute',
              pointerEvents: 'none',
              top: '1rem',
              left: '1rem',
              background: 'rgba(15, 23, 42, 0.8)',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              border: '1px solid #334155',
              color: '#e2e8f0',
              fontSize: '0.8rem'
            }}>
              <strong>{displayNeuron.neuron_id}</strong>
            </div>
          )}
        </section>

        {/* RIGHT PANEL */}
        <aside className="panel right-panel">
          {/* Tab Header: Inspector vs Simulation vs Analysis */}
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
            <button
              className="btn"
              style={{
                flex: 1,
                background: activeRightTab === 'inspector' ? '#1e293b' : 'transparent',
                borderColor: activeRightTab === 'inspector' ? '#38bdf8' : 'transparent',
                color: activeRightTab === 'inspector' ? '#38bdf8' : '#94a3b8',
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '0.35rem 0.3rem',
              }}
              onClick={() => setActiveRightTab('inspector')}
            >
              Inspector
            </button>
            <button
              className="btn"
              style={{
                flex: 1,
                background: activeRightTab === 'simulation' ? '#1e293b' : 'transparent',
                borderColor: activeRightTab === 'simulation' ? '#38bdf8' : 'transparent',
                color: activeRightTab === 'simulation' ? '#38bdf8' : '#94a3b8',
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '0.35rem 0.3rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.3rem',
              }}
              onClick={() => setActiveRightTab('simulation')}
            >
              <span>Simulation</span>
              {simulationResult && (
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#38bdf8' }}></span>
              )}
            </button>
            <button
              className="btn"
              style={{
                flex: 1,
                background: activeRightTab === 'analysis' ? '#1e293b' : 'transparent',
                borderColor: activeRightTab === 'analysis' ? '#38bdf8' : 'transparent',
                color: activeRightTab === 'analysis' ? '#38bdf8' : '#94a3b8',
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '0.35rem 0.3rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.3rem',
              }}
              onClick={() => setActiveRightTab('analysis')}
            >
              <span>Analysis</span>
              {networkAnalysis && (
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#38bdf8' }}></span>
              )}
            </button>
          </div>

          {activeRightTab === 'analysis' ? (
            <NetworkAnalysisPanel
              neurons={filteredNeurons}
              selectedNeuron={selectedNeuron}
              simulationResult={simulationResult}
              onSelectNeuron={handleSelectNeuron}
              analysisResult={networkAnalysis}
              onAnalysisResult={setNetworkAnalysis}
              onGoToSimulation={() => setActiveRightTab('simulation')}
              highlightAffectedOnly={highlightAffectedOnly}
              onToggleHighlightAffected={() => setHighlightAffectedOnly(prev => !prev)}
              activeHopFilter={activeHopFilter}
              onSelectHopFilter={setActiveHopFilter}
            />
          ) : activeRightTab === 'simulation' ? (
            <SimulationPanel
              neurons={filteredNeurons}
              selectedNeuron={selectedNeuron}
              activeFocalId={activeFocalId}
              isRealMode={isRealMode}
              onSelectNeuron={handleSelectNeuron}
              onSimulationResult={res => {
                setSimulationResult(res);
                if (res) {
                  // Reset previous analysis when new simulation runs
                  setNetworkAnalysis(null);
                }
              }}
              onSimulationModeChange={setSimulationMode}
              onTimeStepChange={setCurrentStepIndex}
              simulationResult={simulationResult}
              currentStepIndex={currentStepIndex}
              simMode={simulationMode}
              isPlaying={isPlaying}
              onTogglePlay={() => setIsPlaying(prev => !prev)}
            />
          ) : (
            <>
              <h2 className="panel-title">Inspector</h2>
              
              {!selectedNeuron ? (
                <div style={{ color: '#94a3b8', textAlign: 'center', marginTop: '2rem', fontSize: '0.9rem' }}>
                  SELECT A NEURON
                </div>
              ) : (
                <>
                  <div className="panel-section">
                    <h3>Neuron Properties</h3>
                    <div className="data-row">
                      <span className="data-label">ID</span>
                      <span className="data-value" style={{color: '#38bdf8'}}>{selectedNeuron.neuron_id}</span>
                    </div>
                    <div className="data-row">
                      <span className="data-label">Type</span>
                      <span className="data-value">{selectedNeuron.cell_type}</span>
                    </div>
                    <div className="data-row">
                      <span className="data-label">Region</span>
                      <span className="data-value">{selectedNeuron.region}</span>
                    </div>
                    {selectedNeuron.instance && (
                      <div className="data-row">
                        <span className="data-label">Instance</span>
                        <span className="data-value">{selectedNeuron.instance}</span>
                      </div>
                    )}
                    {selectedNeuron.status && (
                      <div className="data-row">
                        <span className="data-label">Status</span>
                        <span className="data-value">{selectedNeuron.status}</span>
                      </div>
                    )}
                    {selectedNeuron.neurotransmitter && (
                      <div className="data-row">
                        <span className="data-label">Neurotransmitter</span>
                        <span className="data-value" style={{color: '#a3e635'}}>{selectedNeuron.neurotransmitter}</span>
                      </div>
                    )}
                    <div className="data-row">
                      <span className="data-label">Spatial</span>
                      <span className="data-value" style={{color: selectedNeuron.has_coordinates ? '#86efac' : '#94a3b8'}}>
                        {selectedNeuron.has_coordinates ? '3D position available' : 'No spatial data'}
                      </span>
                    </div>
                    <div className="data-row">
                      <span className="data-label">Degree</span>
                      <span className="data-value">{neighborsData ? neighborsData.connections.length : '-'}</span>
                    </div>

                    <button
                      className="btn"
                      style={{ marginTop: '0.5rem', width: '100%', fontSize: '0.8rem', borderColor: '#38bdf8', color: '#38bdf8' }}
                      onClick={() => setActiveRightTab('simulation')}
                    >
                      Use as Simulation Target
                    </button>

                    {isRealMode && selectedNeuron.neuron_id !== activeFocalId && (
                      <button
                        className="btn btn-primary"
                        style={{ marginTop: '0.5rem', width: '100%', fontSize: '0.8rem' }}
                        onClick={() => handleLoadNeighborhood(selectedNeuron.neuron_id, 1)}
                      >
                        Focus Subgraph on this Neuron
                      </button>
                    )}
                  </div>

                  {neighborsData && neighborsData.neurons.length > 1 && (
                    <div className="panel-section">
                      <h3>Connected Neurons</h3>
                      <div className="neighbor-list">
                        {neighborsData.neurons.filter(n => n.neuron_id !== selectedNeuron.neuron_id).slice(0, 10).map(n => (
                          <div 
                            key={n.neuron_id} 
                            className="neighbor-item"
                            onClick={() => handleSelectNeuron(n)}
                          >
                            <span>{n.neuron_id}</span>
                            <span style={{color: '#94a3b8'}}>{n.cell_type}</span>
                          </div>
                        ))}
                        {neighborsData.neurons.length > 11 && (
                          <div className="neighbor-item" style={{justifyContent: 'center', cursor: 'default', background: 'transparent', border: 'none'}}>
                            <span style={{color: '#94a3b8'}}>...and {neighborsData.neurons.length - 11} more</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </aside>
      </main>

      <footer className="bottom-bar">
        <div className="bottom-stat">
          <span>NEURONS:</span>
          <span className="bottom-stat-val">{metadata?.neuron_count !== undefined && metadata.neuron_count >= 0 ? metadata.neuron_count : neurons.length}</span>
        </div>
        <div className="bottom-stat">
          <span>CONNECTIONS:</span>
          <span className="bottom-stat-val">{metadata?.connection_count !== undefined && metadata.connection_count >= 0 ? metadata.connection_count : (isRealMode ? connections.length : 0)}</span>
        </div>
        <div className="bottom-stat">
          <span>SELECTED:</span>
          <span className="bottom-stat-val">{selectedNeuron ? selectedNeuron.neuron_id : '—'}</span>
        </div>
        <div className="bottom-stat">
          <span>VISIBLE CONNECTIONS:</span>
          <span className="bottom-stat-val">{showConnections ? connections.length : 0}</span>
        </div>
        <div className="bottom-stat" style={{marginLeft: 'auto'}}>
          <span>DATASET:</span>
          <span className="bottom-stat-val" style={{color: metadata?.is_synthetic ? '#fca5a5' : '#86efac'}}>
            {metadata?.is_synthetic ? 'SYNTHETIC' : (metadata?.dataset_version ?? 'REAL')}
          </span>
        </div>
      </footer>
    </>
  );
};
