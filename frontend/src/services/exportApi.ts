const API_BASE_URL = "http://127.0.0.1:8000";

export type ExportEndpoint =
  | "customers"
  | "high-risk-customers"
  | "segments"
  | "recommendations"
  | "dashboard-summary";

const exportUrls: Record<ExportEndpoint, string> = {
  customers: `${API_BASE_URL}/api/export/customers.csv`,
  "high-risk-customers": `${API_BASE_URL}/api/export/high-risk-customers.csv`,
  segments: `${API_BASE_URL}/api/export/segments.csv`,
  recommendations: `${API_BASE_URL}/api/export/recommendations.csv`,
  "dashboard-summary": `${API_BASE_URL}/api/export/dashboard-summary.json`,
};

export function downloadExport(endpoint: ExportEndpoint) {
  window.location.href = exportUrls[endpoint];
}