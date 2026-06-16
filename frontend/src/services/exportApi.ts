const API_BASE_URL = "http://127.0.0.1:8000";

export type ExportEndpoint =
  | "high-risk-customers"
  | "segments"
  | "recommendations"
  | "dashboard-summary";

const exportUrls: Record<ExportEndpoint, string> = {
  "high-risk-customers": `${API_BASE_URL}/api/export/high-risk-customers.csv`,
  segments: `${API_BASE_URL}/api/export/segments.csv`,
  recommendations: `${API_BASE_URL}/api/export/recommendations.csv`,
  "dashboard-summary": `${API_BASE_URL}/api/export/dashboard-summary.csv`,
};

type CustomerExportFilters = {
  search?: string;
  riskGroup?: string;
  segment?: string;
  recommendation?: string;
  mainRiskFactor?: string;
  minProbability?: number;
};

export function downloadExport(endpoint: ExportEndpoint) {
  window.location.href = exportUrls[endpoint];
}

export function downloadFilteredCustomers(filters: CustomerExportFilters) {
  const searchParams = new URLSearchParams();

  if (filters.search) {
    searchParams.set("search", filters.search);
  }

  if (filters.riskGroup && filters.riskGroup !== "All") {
    searchParams.set("risk_group", filters.riskGroup);
  }

  if (filters.segment && filters.segment !== "All") {
    searchParams.set("segment", filters.segment);
  }

  if (filters.recommendation && filters.recommendation !== "All") {
    searchParams.set("recommendation", filters.recommendation);
  }

  if (filters.mainRiskFactor && filters.mainRiskFactor !== "All") {
    searchParams.set("main_risk_factor", filters.mainRiskFactor);
  }

  if (filters.minProbability && filters.minProbability > 0) {
    searchParams.set("min_probability", String(filters.minProbability));
  }

  const queryString = searchParams.toString();
  const url = `${API_BASE_URL}/api/export/customers-filtered.csv${
    queryString ? `?${queryString}` : ""
  }`;

  window.location.href = url;
}
