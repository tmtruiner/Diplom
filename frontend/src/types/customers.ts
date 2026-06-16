export type CustomerListItem = {
  customer_id: string;
  churn_probability: number;
  risk_group: "Low" | "Medium" | "High";
  main_risk_factor: string | null;
  estimated_total_charge: number;
  scoring_date: string | null;
  segment_name: string | null;
  recommendation_type: string | null;
  recommendation_reason: string | null;
  priority: "Low" | "Medium" | "High" | null;
  health_score?: number;
  health_status?: CustomerHealthStatus;
  revenue_at_risk?: number;
};

export type CustomerPageFilters = {
  search?: string;
  riskGroup?: string;
  segment?: string;
  recommendation?: string;
  mainRiskFactor?: string;
  minProbability?: number;
};

export type CustomerFilterOptions = {
  risk_groups: string[];
  segments: string[];
  recommendations: string[];
  main_risk_factors: string[];
};

export type CustomersResponse = {
  items: CustomerListItem[];
  total: number;
  limit?: number;
  offset?: number;
};

export type CustomerDetail = {
  customer_id: string;

  prediction: {
    churn_probability: number;
    risk_group: string;
    main_risk_factor: string;
    estimated_total_charge: number;
    scoring_date: string | null;
  };

  segment: {
    segment_id: number | null;
    segment_name: string;
  };

  recommendation: {
    recommendation_type: string;
    recommendation_reason: string | null;
    priority: string | null;
  };

  health: CustomerHealth;
};

export type HealthTone = "red" | "amber" | "blue" | "green";

export type CustomerHealthStatus = {
  code: string;
  label: string;
  tone: HealthTone;
};

export type CustomerRiskDriver = {
  code: string;
  value: string | number | null;
  label: string;
  impact: string;
};

export type CustomerHealth = {
  score: number;
  status: CustomerHealthStatus;
  revenue_at_risk: number;
  risk_drivers: CustomerRiskDriver[];
  next_best_action: {
    recommendation_type: string;
    recommendation_reason: string | null;
    priority: string | null;
  };
  expected_effect: {
    risk_reduction_potential: string;
    processing_priority: number;
  };
};
