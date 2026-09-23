import { useEffect, useState } from "react";
import { checkHealth } from "./api/client";
import { ConnectomeViewer } from "./components/ConnectomeViewer";
import "./App.css";

type ConnectionStatus = "loading" | "connected" | "disconnected";

function App() {
  const [status, setStatus] = useState<ConnectionStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchHealth() {
      try {
        await checkHealth();
        if (!cancelled) {
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

  if (status === "loading") {
    return (
      <div className="loading-screen">
        <h2>Drosophila-NeuroAtlas</h2>
        <p>Connecting to computational backend...</p>
      </div>
    );
  }

  if (status === "disconnected") {
    return (
      <div className="error-screen">
        <h2>System Disconnected</h2>
        <p>{error || "Failed to reach backend."}</p>
        <p style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
          Ensure the server is running at http://localhost:8000
        </p>
      </div>
    );
  }

  return (
    <div className="app">
      <ConnectomeViewer />
    </div>
  );
}

export default App;
