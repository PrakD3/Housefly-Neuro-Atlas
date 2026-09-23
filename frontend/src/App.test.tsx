import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "./App";
import { checkHealth } from "./api/client";

// Mock the API client
vi.mock("./api/client", () => ({
  checkHealth: vi.fn(),
}));

// Mock ConnectomeViewer to avoid loading three.js in tests
vi.mock("./components/ConnectomeViewer", () => ({
  ConnectomeViewer: () => <div data-testid="connectome-viewer">ConnectomeViewer Mock</div>
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading screen initially", () => {
    vi.mocked(checkHealth).mockResolvedValue({ status: "ok" });
    render(<App />);
    expect(screen.getByText("Connecting to computational backend...")).toBeInTheDocument();
  });

  it("shows ConnectomeViewer when backend responds", async () => {
    vi.mocked(checkHealth).mockResolvedValue({ status: "ok" });
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTestId("connectome-viewer")).toBeInTheDocument();
    });
  });

  it("shows disconnected status when backend fails", async () => {
    vi.mocked(checkHealth).mockRejectedValue(new Error("Network error"));
    render(<App />);
    
    const disconnected = await screen.findByText("System Disconnected");
    expect(disconnected).toBeInTheDocument();
  });
});
