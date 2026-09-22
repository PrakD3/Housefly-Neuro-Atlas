import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "./App";

// Mock the API client
vi.mock("./api/client", () => ({
  checkHealth: vi.fn(),
}));

import { checkHealth } from "./api/client";

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the project title", async () => {
    vi.mocked(checkHealth).mockResolvedValue({ status: "ok" });
    render(<App />);
    expect(
      screen.getByText("Drosophila-NeuroAtlas")
    ).toBeInTheDocument();
  });

  it("shows connected status when backend responds", async () => {
    vi.mocked(checkHealth).mockResolvedValue({ status: "ok" });
    render(<App />);
    const connected = await screen.findByText("● Connected");
    expect(connected).toBeInTheDocument();
  });

  it("shows disconnected status when backend fails", async () => {
    vi.mocked(checkHealth).mockRejectedValue(new Error("Network error"));
    render(<App />);
    const disconnected = await screen.findByText("○ Disconnected");
    expect(disconnected).toBeInTheDocument();
  });
});
