export type RecommendationItem = {
  recommendation_type: string;
  customers_count: number;
  high_risk_customers: number;
  high_priority_customers: number;
  average_churn_probability: number;
  high_risk_share: number;
  estimated_revenue_at_risk: number;
  recommendation_reason: string | null;
  priority: "Low" | "Medium" | "High" | null;
  main_risk_factor: string | null;
};

export type RecommendationsResponse = {
  items: RecommendationItem[];
};