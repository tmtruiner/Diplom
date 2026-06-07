import type {
  CustomerDetail,
  CustomerFilterOptions,
  CustomersResponse,
} from "../types/customers";

const API_BASE_URL = "http://127.0.0.1:8000";

type FetchCustomersParams = {
  search?: string;
  riskGroup?: string;
  segment?: string;
  recommendation?: string;
  mainRiskFactor?: string;
  minProbability?: number;
};

export async function fetchCustomers(
  params?: FetchCustomersParams
): Promise<CustomersResponse> {
  const searchParams = new URLSearchParams();

  if (params?.search) {
    searchParams.set("search", params.search);
  }

  if (params?.riskGroup && params.riskGroup !== "All") {
    searchParams.set("risk_group", params.riskGroup);
  }

  if (params?.segment && params.segment !== "All") {
    searchParams.set("segment", params.segment);
  }

  if (params?.recommendation && params.recommendation !== "All") {
    searchParams.set("recommendation", params.recommendation);
  }

  if (params?.mainRiskFactor && params.mainRiskFactor !== "All") {
    searchParams.set("main_risk_factor", params.mainRiskFactor);
  }

  if (params?.minProbability && params.minProbability > 0) {
    searchParams.set("min_probability", String(params.minProbability));
  }

  const queryString = searchParams.toString();

  const response = await fetch(
    `${API_BASE_URL}/api/customers${queryString ? `?${queryString}` : ""}`
  );

  if (!response.ok) {
    throw new Error("Failed to load customers");
  }

  const data = await response.json();

  if (Array.isArray(data)) {
    return {
      items: data,
    };
  }

  return {
    items: data.items ?? [],
  };
}

export async function fetchCustomerDetail(
  customerId: string
): Promise<CustomerDetail> {
  const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}`);

  if (!response.ok) {
    throw new Error("Failed to load customer detail");
  }

  return response.json();
}

export async function fetchCustomerFilterOptions(): Promise<CustomerFilterOptions> {
  const response = await fetch(`${API_BASE_URL}/api/customers/filter-options`);

  if (!response.ok) {
    throw new Error("Failed to load customer filter options");
  }

  const data = await response.json();

  return {
    risk_groups: data.risk_groups ?? [],
    segments: data.segments ?? [],
    recommendations: data.recommendations ?? [],
  };
}