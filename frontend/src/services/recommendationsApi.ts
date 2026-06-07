import type { RecommendationsResponse } from "../types/recommendations";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchRecommendations(): Promise<RecommendationsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/recommendations`);

  if (!response.ok) {
    throw new Error("Failed to load recommendations");
  }

  return response.json();
}