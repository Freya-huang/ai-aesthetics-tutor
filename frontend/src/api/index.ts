import client from './client';
import type {
  HealthStatus,
  KnowledgeStatus,
  ArtDiagnosisOutput,
  PaperInterpretOutput,
  FollowupResponse,
  ArtworkType,
  SourceCard,
} from '@/types';

export async function getHealth(): Promise<HealthStatus> {
  const response = await client.get<HealthStatus>('/health');
  return response.data;
}

export async function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  const response = await client.get<{ success: boolean; data: KnowledgeStatus }>('/knowledge/status');
  return response.data.data;
}

export async function searchKnowledge(
  query: string,
  category?: string,
  top_k: number = 3
): Promise<SourceCard[]> {
  const params: Record<string, string | number> = { query, top_k };
  if (category) {
    params.category = category;
  }
  const response = await client.get<{ success: boolean; data: SourceCard[] }>('/knowledge/search', {
    params,
  });
  return response.data.data;
}

export interface DiagnoseArtParams {
  image: File;
  artwork_type?: ArtworkType;
  scene?: string;
  intent?: string;
  focus_points?: string[];
  session_id?: string;
}

export async function diagnoseArt(params: DiagnoseArtParams): Promise<ArtDiagnosisOutput> {
  const formData = new FormData();
  formData.append('image', params.image);
  if (params.artwork_type) {
    formData.append('artwork_type', params.artwork_type);
  }
  if (params.scene) {
    formData.append('scene', params.scene);
  }
  if (params.intent) {
    formData.append('intent', params.intent);
  }
  if (params.focus_points && params.focus_points.length > 0) {
    formData.append('focus_points', params.focus_points.join(','));
  }
  if (params.session_id) {
    formData.append('session_id', params.session_id);
  }
  const response = await client.post<ArtDiagnosisOutput>('/art-diagnosis/diagnose', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function followupArt(
  session_id: string,
  question: string,
  knowledge_point_name?: string
): Promise<FollowupResponse> {
  const response = await client.post<FollowupResponse>('/art-diagnosis/followup', {
    session_id,
    question,
    knowledge_point_name,
  });
  return response.data;
}

export interface InterpretPaperParams {
  pdf_file: File;
  reading_purpose?: string;
  focus_questions?: string[];
  session_id?: string;
}

export async function interpretPaper(params: InterpretPaperParams): Promise<PaperInterpretOutput> {
  const formData = new FormData();
  formData.append('pdf_file', params.pdf_file);
  if (params.reading_purpose) {
    formData.append('reading_purpose', params.reading_purpose);
  }
  if (params.focus_questions && params.focus_questions.length > 0) {
    formData.append('focus_questions', params.focus_questions.join(','));
  }
  if (params.session_id) {
    formData.append('session_id', params.session_id);
  }
  const response = await client.post<PaperInterpretOutput>('/paper-interpreter/interpret', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function followupPaper(
  session_id: string,
  question: string
): Promise<FollowupResponse> {
  const response = await client.post<FollowupResponse>('/paper-interpreter/followup', {
    session_id,
    question,
  });
  return response.data;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  type: string;
  content: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface ChatResponseData {
  session_id: string;
  reply: string;
  reply_type: string;
  detected_intent: string;
  requires_more_info: boolean;
  clarification_question?: string;
  diagnosis_result?: ArtDiagnosisOutput;
  interpret_result?: PaperInterpretOutput;
  suggested_actions?: string[];
}

export interface SendChatParams {
  session_id?: string;
  message: string;
  image?: File;
  pdf?: File;
  followup_type?: 'image' | 'pdf';
  followup_session_id?: string;
}

export async function sendChatMessage(params: SendChatParams): Promise<ChatResponseData> {
  const formData = new FormData();
  if (params.session_id) {
    formData.append('session_id', params.session_id);
  }
  formData.append('message', params.message);
  if (params.image) {
    formData.append('image', params.image);
  }
  if (params.pdf) {
    formData.append('pdf', params.pdf);
  }
  if (params.followup_type) {
    formData.append('followup_type', params.followup_type);
  }
  if (params.followup_session_id) {
    formData.append('followup_session_id', params.followup_session_id);
  }
  const response = await client.post<ChatResponseData>('/chat/send', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}

export interface ChatHistoryMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  type: string;
  content: string;
  timestamp: number;
  attachments?: Array<{ type: 'image' | 'pdf'; filename: string }>;
  metadata?: { result_type?: 'art' | 'paper'; result?: ArtDiagnosisOutput | PaperInterpretOutput };
}

export interface ArchivedReport {
  report_id: string;
  source_session_id: string;
  chat_session_id?: string;
  report_type: 'art' | 'paper';
  title: string;
  result: ArtDiagnosisOutput | PaperInterpretOutput;
  created_at: number;
}

export async function getChatSessions(): Promise<ChatSessionSummary[]> {
  const response = await client.get<{ sessions: ChatSessionSummary[] }>('/chat/sessions');
  return response.data.sessions;
}

export async function getChatHistory(sessionId: string): Promise<ChatHistoryMessage[]> {
  const response = await client.get<{ messages: ChatHistoryMessage[] }>(`/chat/history/${sessionId}`);
  return response.data.messages;
}

export async function renameChatSession(sessionId: string, title: string): Promise<void> {
  await client.patch(`/chat/sessions/${sessionId}`, { title });
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await client.delete(`/chat/sessions/${sessionId}`);
}

export async function listArchivedReports(): Promise<ArchivedReport[]> {
  const response = await client.get<{ reports: ArchivedReport[] }>('/chat/reports');
  return response.data.reports;
}

export async function archiveReport(
  reportType: 'art' | 'paper',
  title: string,
  result: ArtDiagnosisOutput | PaperInterpretOutput,
  chatSessionId?: string
): Promise<ArchivedReport> {
  const response = await client.post<ArchivedReport>('/chat/reports', {
    report_type: reportType,
    title,
    result,
    chat_session_id: chatSessionId,
  });
  return response.data;
}

export async function deleteArchivedReport(reportId: string): Promise<void> {
  await client.delete(`/chat/reports/${reportId}`);
}
