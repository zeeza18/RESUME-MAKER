export interface TailorRequest {
  jobDescription: string;
  currentResume: string;
}

export interface KeywordAnalysis {
  keywords?: string[];
  needs?: string[];
  results?: string[];
  raw_analysis?: string;
  error?: string;
}

export interface EvaluationResult {
  score?: number;
  experience_evaluation?: string;
  ats_optimization?: string;
  feedback?: string;
  recommendations?: string[];
  raw_evaluation?: string;
}

export interface TailorResponse {
  status: string;
  final_resume: string;
  final_score: number;
  keyword_analysis: KeywordAnalysis;
  all_evaluations: EvaluationResult[];
  job_description: string;
  original_resume: string;
  best_round?: number;
  best_evaluation?: EvaluationResult;
}

export type ApiError = {
  message: string;
  details?: string;
};
export type TailorStreamEvent =
  | {
      event: 'keywords_extracted';
      status?: string;
      keyword_analysis: KeywordAnalysis;
      job_description: string;
      original_resume: string;
    }
  | {
      event: 'round_complete';
      status?: string;
      round: number;
      keyword_analysis: KeywordAnalysis;
      tailored_resume?: string;
      change_log?: string[];
      evaluation: EvaluationResult;
      all_evaluations: EvaluationResult[];
    }
  | {
      event: 'complete';
      payload: TailorResponse;
    }
  | {
      event: 'error';
      message: string;
    };

