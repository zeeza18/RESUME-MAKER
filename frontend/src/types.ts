export interface TailorRequest {
  jobDescription: string;
  currentResume: string;
}

// Job Application Types
export interface Job {
  id: string;
  url: string;
  company: string;
  notes: string;
  status: 'pending' | 'applied' | 'failed' | 'in_progress';
  date_added: string;
  date_applied: string | null;
  attempts: number;
  last_error: string | null;
}

export interface ATSCheckResult {
  keywords: KeywordAnalysis;
  evaluation: EvaluationResult;
  score: number;
  status: string;
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

// Auto-apply pipeline types
export type ApplyPhase = 'jd_extraction' | 'tailoring' | 'pdf_compilation' | 'form_filling';

export type ApplyStreamEvent =
  | { event: 'started'; job_id: string; url: string }
  | { event: 'phase'; phase: ApplyPhase; message: string }
  | { event: 'progress'; phase?: ApplyPhase; message: string }
  | { event: 'jd_extracted'; phase: 'jd_extraction'; job_description: string; job_title: string; company: string; confidence: number; message: string }
  | { event: 'tailoring_round_complete'; phase: 'tailoring'; round: number; score: number; message: string }
  | { event: 'tailoring_complete'; phase: 'tailoring'; score: number; message: string }
  | { event: 'pdf_compiled'; phase: 'pdf_compilation'; pdf_path: string; message: string }
  | { event: 'complete'; success: boolean; message?: string; errors?: string[] }
  | { event: 'error'; phase?: string; message: string };

