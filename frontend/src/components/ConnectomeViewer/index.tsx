import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { 
  getConnectomeInfo, 
  getNeurons, 
  getNeuronNeighbors,
  Neuron, 
  Connection, 
  ConnectomeMetadata, 
  SubgraphResponse 
} from '../../api/client';
import { Scene } from './Scene';

export const ConnectomeViewer: React.FC = () => {
  const [metadata, setMetadata] = useState<ConnectomeMetadata | null>(null);
  const [neurons, setNeurons] = useState<Neuron[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedNeuron, setSelectedNeuron] = useState<Neuron | null>(null);
  const [hoveredNeuron, setHoveredNeuron] = useState<Neuron | null>(null);
  const [neighborsData, setNeighborsData] = useState<SubgraphResponse | null>(null);
  const [showConnections, setShowConnections] = useState<boolean>(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [cellTypeFilter, setCellTypeFilter] = useState("All");
  const [regionFilter, setRegionFilter] = useState("All");

  const [canvasKey, setCanvasKey] = useState<number>(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const info = await getConnectomeInfo();
        setMetadata(info);

        const allNeurons = await getNeurons();
        setNeurons(allNeurons);
        
        // For Phase 2, we load connections when a neuron is selected.
        setLoading(false);
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    const fetchNeighbors = async () => {
      if (selectedNeuron) {
        try {
          const data = await getNeuronNeighbors(selectedNeuron.neuron_id, 1);
          setNeighborsData(data);
          setConnections(data.connections);
        } catch (err) {
          console.error("Failed to fetch neighbors", err);
        }
      } else {
        setNeighborsData(null);
        setConnections([]);
      }
    };
    fetchNeighbors();
  }, [selectedNeuron]);

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

  const displayNeuron = hoveredNeuron || selectedNeuron;
  
  // Calculate unique cell types and regions
  const cellTypes = useMemo(() => ["All", ...Array.from(new Set(neurons.map(n => n.cell_type))).sort()], [neurons]);
  const regions = useMemo(() => ["All", ...Array.from(new Set(neurons.map(n => n.region))).sort()], [neurons]);

  // Apply filters
  const filteredNeurons = useMemo(() => {
    return neurons.filter(n => {
      if (searchQuery && !n.neuron_id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      if (cellTypeFilter !== "All" && n.cell_type !== cellTypeFilter) return false;
      if (regionFilter !== "All" && n.region !== regionFilter) return false;
      return true;
    });
  }, [neurons, searchQuery, cellTypeFilter, regionFilter]);

  // Compute bounding box for camera framing
  const boundingBox = useMemo(() => {
    if (filteredNeurons.length === 0) {
      return { center: [0, 0, 0] as [number, number, number], width: 40, height: 40, depth: 40, maxDimension: 40 };
    }
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;
    
    for (const n of filteredNeurons) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
      if (n.z < minZ) minZ = n.z;
      if (n.z > maxZ) maxZ = n.z;
    }
    
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const cz = (minZ + maxZ) / 2;
    
    const width = maxX === -Infinity ? 40 : maxX - minX;
    const height = maxY === -Infinity ? 40 : Math.max(maxY - minY, 1);
    const depth = maxZ === -Infinity ? 40 : maxZ - minZ;
    
    const maxDimension = Math.max(width, height, depth) || 40;
    
    return { center: [cx, cy, cz] as [number, number, number], width, height, depth, maxDimension };
  }, [filteredNeurons]);


  if (loading) return <div className="loading-screen">Loading Connectome Data...</div>;
  if (error) return <div className="error-screen">Error loading data: {error}</div>;



  // Color mapping for the legend
  const cellTypeColors: Record<string, string> = {
    "Sensory": "#fbbf24",     // yellow
    "Interneuron": "#a78bfa", // purple
    "Projection": "#f87171",  // red
    "Motor": "#34d399",       // green
    "Modulatory": "#38bdf8",  // cyan
  };

  return (
    <>
      <header className="app-header">
        <div className="header-title">
          <h1>Drosophila-NeuroAtlas</h1>
          <p className="subtitle">Connectome-driven computational neuroscience platform</p>
        </div>
        {metadata?.is_synthetic && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
            <div className="header-status">
              SYNTHETIC DATA
            </div>
            <p style={{fontSize: '0.7rem', color: '#94a3b8', margin: '4px 0 0 0', textTransform: 'uppercase', letterSpacing: '0.05em'}}>
              Synthetic spatial layout — not anatomical coordinates
            </p>
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
              <span className="data-value">Synthetic</span>
            </div>
            <div className="data-row">
              <span className="data-label">Status</span>
              <span className="data-value" style={{color: '#fca5a5'}}>Software Test Data</span>
            </div>
          </div>

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

            <button className="btn btn-primary" style={{marginTop: '0.5rem'}} onClick={toggleConnections}>
              {showConnections ? "Hide Connections" : "Show Connections"}
            </button>
            <button className="btn" onClick={resetCamera}>
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
        <section className="viewport">
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
                <div className="data-row">
                  <span className="data-label">Degree</span>
                  <span className="data-value">{neighborsData ? neighborsData.connections.length : '-'}</span>
                </div>
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
        </aside>
      </main>

      <footer className="bottom-bar">
        <div className="bottom-stat">
          <span>NEURONS:</span>
          <span className="bottom-stat-val">{metadata?.neuron_count || 0}</span>
        </div>
        <div className="bottom-stat">
          <span>CONNECTIONS:</span>
          <span className="bottom-stat-val">{metadata?.connection_count || 0}</span>
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
          <span className="bottom-stat-val" style={{color: '#fca5a5'}}>SYNTHETIC</span>
        </div>
      </footer>
    </>
  );
};
