export interface RetrievedEvidence {
  conversation_id: string;
  customer_issue: string;
  historical_agent_response: string;
  similarity_score: number;
  intent: string;
  timestamp: string;
}

export interface ClassificationResult {
  intent: string;
  confidence: number;
  reason: string;
  source: string;
}

export interface EscalationResult {
  decision: "AUTO-HANDLE" | "ESCALATE";
  reason: string;
  all_reasons: string[];
  risk_factors: string[];
  confidence_score: number;
  similarity_score: number;
}

export interface ExplanationPayload {
  intent_detected: string;
  intent_confidence: number;
  classification_source: string;
  escalation_decision: string;
  escalation_reason: string;
  risk_factors_triggered: string[];
  retrieved_precedent_id: string;
  retrieval_similarity: number;
  safety_policy_passed: boolean;
  generation_engine: string;
}

export interface AgentResponse {
  brand: string;
  raw_input: string;
  cleaned_input: string;
  classification: ClassificationResult;
  evidence_sufficiency: {
    sufficient: boolean;
    max_similarity: number;
    threshold: number;
    reason: string;
  };
  retrieved_evidence: RetrievedEvidence[];
  escalation: EscalationResult;
  generated_reply: string;
  explanation: ExplanationPayload;
}

export interface EvaluationMetrics {
  dataset_name: string;
  evaluation_sample_size: number;
  brand: string;
  intent_classification: {
    dataset: string;
    sample_size: number;
    majority_baseline: {
      accuracy: number;
      macro_precision: number;
      macro_recall: number;
      macro_f1: number;
    };
    tfidf_logistic_baseline: {
      accuracy: number;
      macro_precision: number;
      macro_recall: number;
      macro_f1: number;
    };
    ai_intent_classifier: {
      accuracy: number;
      macro_precision: number;
      macro_recall: number;
      macro_f1: number;
    };
  };
  escalation_safety: {
    dataset: string;
    total_samples: number;
    ground_truth_escalations: number;
    ground_truth_autohandle: number;
    metrics: {
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
    };
    confusion_matrix: {
      true_negatives: number;
      false_positives: number;
      false_negatives: number;
      true_positives: number;
      over_escalation_rate: number;
      missed_escalation_rate: number;
    };
    business_cost_analysis: {
      cost_per_false_positive_usd: number;
      cost_per_false_negative_usd: number;
      pipeline_total_cost_usd: number;
      baseline_100pct_human_cost_usd: number;
      baseline_zero_escalation_risk_cost_usd: number;
      net_savings_over_human_usd: number;
      automation_containment_rate: number;
    };
  };
  llm_judge: {
    evaluated_samples: number;
    overall_rubric_average: number;
    dimension_averages: {
      correctness: number;
      groundedness: number;
      relevance: number;
      helpfulness: number;
      brand_consistency: number;
      safety: number;
    };
  };
  human_llm_agreement: {
    exact_agreement_rate: number;
    within_one_point_agreement_rate: number;
    pearson_correlation: number;
    spearman_correlation: number;
    mean_absolute_error: number;
    disagreement_analysis: {
      leniency_bias: string;
      human_strictness: string;
      safety_consensus: string;
    };
  };
}

export interface FailureCase {
  failure_id: number;
  category: string;
  customer_input: string;
  expected_output: any;
  actual_output: any;
  why_it_failed_hypothesis: string;
  how_to_fix: string;
}

export interface GoldenSample {
  id: string;
  customer_message: string;
  ground_truth_intent: string;
  historical_agent_reply: string;
  ground_truth_escalate: boolean;
}
