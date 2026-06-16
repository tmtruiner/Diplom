export type DashboardSummary = {
  kpis: {
    total_customers: number;
    high_risk_customers: number;
    average_churn_probability: number;
    estimated_revenue_at_risk: number;
    last_scoring_date: string | null;
  };

  risk_distribution: {
    risk_group: "Low" | "Medium" | "High";
    customers_count: number;
  }[];

  average_churn_by_segment: {
    segment: string;
    average_churn_probability: number;
  }[];

  high_risk_share_by_segment: {
    segment: string;
    high_risk_share: number;
  }[];

  recommendations_summary: {
    recommendation_type: string;
    customers_count: number;
  }[];

  top_risk_factors: {
    factor: string;
    customers_count: number;
    high_risk_share: number;
    impact: "Low" | "Medium" | "High";
  }[];

  priority_segments: {
    segment: string;
    clients_count: number;
    average_churn_probability: number;
    high_risk_share: number;
    main_risk_factor: string;
    main_recommendation: string;
  }[];

  scoring_info: {
    model_name: string | null;
    model_version: string | null;
    algorithm: string | null;
    roc_auc: number | null;
    f1_score: number | null;
    recall: number | null;
    high_risk_threshold: number;
    medium_risk_threshold: number;
    last_scoring_date: string | null;
    last_training_date: string | null;
  };
};
