import type { DashboardSummary } from "../types/dashboard";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/summary`);

  if (!response.ok) {
    throw new Error("Failed to load dashboard summary");
  }

  return response.json();
}