export type SegmentItem = {
  segment_name: string;
  clients_count: number;
  high_risk_customers: number;
  average_churn_probability: number;
  high_risk_share: number;
  average_estimated_total_charge: number;
  main_recommendation: string | null;
  main_risk_factor: string | null;
};

export type SegmentsResponse = {
  items: SegmentItem[];
};

export type SegmentCustomer = {
  customer_id: string;
  churn_probability: number;
  risk_group: "Low" | "Medium" | "High";
  main_risk_factor: string | null;
  estimated_total_charge: number;
  scoring_date: string | null;
  segment_name: string;
  recommendation_type: string | null;
  recommendation_reason: string | null;
  priority: "Low" | "Medium" | "High" | null;
};

export type SegmentCustomersResponse = {
  items: SegmentCustomer[];
};
