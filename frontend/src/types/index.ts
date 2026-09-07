export type Language = "python" | "javascript" | "typescript" | "java" | "cpp" | "c";
export type Difficulty = "beginner" | "intermediate" | "advanced";

export type BugType =
  | "syntax"
  | "runtime"
  | "logic"
  | "edge_case"
  | "performance"
  | "security"
  | "quality";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Bug {
  title: string;
  type: BugType;
  severity: Severity;
  line: number | null;
  verified: boolean;
  problem: string;
  explanation: string;
  suggested_fix: string;
}

export type AnalysisStatus = "success" | "partial" | "error";

export interface StaticAnalysisFinding {
  title: string;
  severity: Severity;
  line: number | null;
  message: string;
}

export interface StaticAnalysisResult {
  language: string;
  syntax_valid: boolean;
  findings: StaticAnalysisFinding[];
  fully_supported: boolean;
}

export interface MentorAnalysis {
  language: string;
  summary: string;
  code_quality_score: number;
  analysis_status: AnalysisStatus;
  bugs: Bug[];
  strengths: string[];
  fixed_code: string;
  changes: string[];
  tests: string;
  test_explanations: string[];
  edge_cases: string[];
  learning_points: string[];
  next_exercise: string;
}

export interface AnalyzeResponse {
  static_analysis: StaticAnalysisResult;
  mentor: MentorAnalysis;
  disclaimer: string;
}

export interface AnalyzeRequestBody {
  code: string;
  language: Language;
  difficulty: Difficulty;
  question?: string;
}

export interface ApiErrorShape {
  status: number;
  message: string;
}
