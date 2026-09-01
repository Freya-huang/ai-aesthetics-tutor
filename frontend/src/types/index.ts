export type ArtworkType = 'painting' | 'digital_art' | 'photography' | 'sketch' | 'poster' | 'ppt' | 'other';

export interface SourceCard {
  source_id: string;
  title: string;
  category: string;
  snippet: string;
  relevance: number;
}

export interface KnowledgePoint {
  name: string;
  source_id: string;
  description: string;
}

export interface ArtDiagnosisOutput {
  creative_goal: string;
  visual_observations: string;
  strengths: string[];
  key_learning: string;
  aesthetics_knowledge: string;
  multiple_perspectives: string[];
  revision_tasks: string[];
  reflection_questions: string[];
  usage_boundaries: string;
  sources: SourceCard[];
  recommended_knowledge: KnowledgePoint[];
  session_id: string;
}

export interface PageCitation {
  page_number: number;
  quote_snippet: string;
}

export interface PaperImageRef {
  image_id: string;
  page_number: number;
  description: string;
  observation: string;
}

export interface PaperInterpretOutput {
  one_sentence_summary?: string;
  core_questions?: string[];
  core_viewpoints?: string[];
  argument_process?: string[];
  course_creation_connections?: string[];
  next_reflection_task?: string;
  literature_info: string;
  core_thesis: string;
  research_questions: string[];
  key_concepts: Array<{ name: string; description: string; page_number?: number; citations?: PageCitation[] }>;
  argument_structure: Array<{ section: string; summary: string; page?: number }>;
  classical_connections: Array<{ topic: string; connection: string }>;
  paper_images: PaperImageRef[];
  contributions_limitations: string;
  recommended_reading: KnowledgePoint[];
  sources: {
    page_citations?: PageCitation[];
    rag_sources?: SourceCard[];
    [key: string]: unknown;
  };
  session_id: string;
}

export interface FollowupResponse {
  answer: string;
  session_id: string;
}

export interface HealthStatus {
  status: string;
  app_name: string;
  mock_mode: boolean;
  version: string;
}

export interface KnowledgeStatus {
  total_documents?: number;
  total_chunks?: number;
  categories?: Record<string, number>;
  [key: string]: unknown;
}

export interface ApiError {
  detail?: string;
  message?: string;
}
