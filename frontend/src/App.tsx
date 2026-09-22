import { useEffect, useState } from "react";
import { checkHealth, type HealthResponse } from "./api/client";
import { ConnectomeViewer } from "./components/ConnectomeViewer";
import "./App.css";

type ConnectionStatus = "loading" | "connected" | "disconnected";

function App() {
  const [status, setStatus] = useState<ConnectionStatus>("loading");
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchHealth() {
      try {
        const data = await checkHealth();
        if (!cancelled) {
          setHealthData(data);
          setStatus("connected");
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setStatus("disconnected");
          setError(
            err instanceof Error ? err.message : "Failed to connect to backend"
          );
        }
      }
    }

    fetchHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="app">
      {status === "connected" ? (
        <div className="viewer-container">
          <ConnectomeViewer />
        </div>
      ) : (
        <>
          <header className="app-header">
            <h1>Drosophila-NeuroAtlas</h1>
            <p className="subtitle">
              Connectome-driven computational neuroscience platform
            </p>
          </header>
          <main className="app-main">
            <section className="status-card">
              <h2>System Status</h2>

              <div className="status-row">
                <span className="status-label">Backend</span>
                <span className={`status-indicator status-${status}`}>
                  {status === "loading" && "⏳ Checking…"}
                  {status === "disconnected" && "○ Disconnected"}
                </span>
              </div>

              {healthData && (
                <div className="status-row">
                  <span className="status-label">Health</span>
                  <span className="status-value">{healthData.status}</span>
                </div>
              )}

              {error && (
                <div className="error-message">
                  <p>{error}</p>
                  <p className="hint">
                    Make sure the backend is running on{" "}
                    <code>http://localhost:8000</code>
                  </p>
                </div>
              )}
            </section>
          </main>
          <footer className="app-footer">
            <p>Drosophila-NeuroAtlas v0.1.0</p>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;
