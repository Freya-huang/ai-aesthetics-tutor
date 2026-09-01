import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Bot,
  BookOpen,
  FileText,
  History,
  Image as ImageIcon,
  Loader2,
  Menu,
  PlusCircle,
  Palette,
  Pencil,
  Send,
  Sparkles,
  ScanSearch,
  Trash2,
  User as UserIcon,
  X,
} from 'lucide-react';
import {
  deleteChatSession,
  getChatHistory,
  getChatSessions,
  renameChatSession,
  sendChatMessage,
  type ChatHistoryMessage,
  type ChatResponseData,
  type ChatSessionSummary,
} from '@/api';
import type { ArtDiagnosisOutput, KnowledgePoint, PaperInterpretOutput } from '@/types';
import DiagnosisResult from '@/components/DiagnosisResult';
import InterpretResult from '@/components/InterpretResult';
import ChatMarkdown from '@/components/ChatMarkdown';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  imageFile?: { name: string; preview?: string };
  pdfFile?: { name: string };
  diagnosisResult?: ArtDiagnosisOutput;
  interpretResult?: PaperInterpretOutput;
  suggestedActions?: string[];
  isError?: boolean;
  isWelcome?: boolean;
}

const MAX_IMAGE_SIZE = 10 * 1024 * 1024;
const MAX_PDF_SIZE = 50 * 1024 * 1024;
const ACTIVE_SESSION_KEY = 'aesthetics-tutor-active-session';

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: '从一件作品、一个问题，或一篇论文开始。',
  timestamp: Date.now() / 1000,
  isWelcome: true,
};

function historyMessageToChat(message: ChatHistoryMessage): ChatMessage | null {
  if (message.role === 'system') return null;
  const imageAttachment = message.attachments?.find((item) => item.type === 'image');
  const pdfAttachment = message.attachments?.find((item) => item.type === 'pdf');
  const resultType = message.metadata?.result_type;
  const result = message.metadata?.result;
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    timestamp: message.timestamp,
    imageFile: imageAttachment ? { name: imageAttachment.filename } : undefined,
    pdfFile: pdfAttachment ? { name: pdfAttachment.filename } : undefined,
    diagnosisResult: resultType === 'art' ? result as ArtDiagnosisOutput : undefined,
    interpretResult: resultType === 'paper' ? result as PaperInterpretOutput : undefined,
    suggestedActions: message.metadata?.knowledge_suggestions,
    isWelcome: message.type === 'welcome',
  };
}

function WelcomePanel({ composer, onSelect }: { composer?: ReactNode; onSelect: (prompt: string) => void }) {
  const capabilities = [
    { icon: ScanSearch, title: '欣赏一幅作品', text: '从构图、色彩与光影开始观察', prompt: '请引导我分析一件作品的构图、色彩和光影。' },
    { icon: BookOpen, title: '研读一篇论文', text: '梳理论点、概念、证据与学术脉络', prompt: '我想研读一篇美学论文，请帮我建立阅读框架。' },
    {
      icon: Sparkles,
      title: '美学概念解读',
      text: '用双层解释法，从生活类比进入专业理论',
      prompt: '我想学习一个美学概念。\n概念或问题：【填写概念或问题】\n希望联系的方向：艺术作品',
    },
  ];
  return (
    <div className="chat-welcome-panel">
      <div className="chat-welcome-symbol" aria-hidden="true">
        <span className="chat-welcome-symbol-side"><ScanSearch size={16} strokeWidth={1.6} /></span>
        <span className="chat-welcome-symbol-main"><Palette size={28} strokeWidth={1.5} /></span>
        <span className="chat-welcome-symbol-side"><BookOpen size={16} strokeWidth={1.6} /></span>
      </div>
      <span className="chat-welcome-eyebrow">PRIVATE AESTHETICS STUDIO</span>
      <h2>今天想从哪里开始？</h2>
      <p>带来一件作品、一篇论文，或一个正在困扰你的美学问题。</p>
      {composer && <div className="chat-welcome-composer">{composer}</div>}
      <div className="chat-welcome-capabilities">
        {capabilities.map(({ icon: Icon, title, text, prompt }) => (
          <button key={title} type="button" className="chat-welcome-capability" onClick={() => onSelect(prompt)}>
            <span><Icon size={19} strokeWidth={1.6} /></span>
            <strong>{title}</strong>
            <small>{text}</small>
          </button>
        ))}
      </div>
    </div>
  );
}

function actionsForMessage(message: ChatMessage): string[] {
  const recommended = message.diagnosisResult?.recommended_knowledge
    || message.interpretResult?.recommended_reading
    || [];
  const explainActions = recommended.slice(0, 2).map((point) => `解释「${point.name}」`);
  if (message.diagnosisResult) return [...explainActions, '生成一个针对性练习', '给我一个修改示例'];
  if (message.interpretResult) return [...explainActions, '生成阅读提纲', '给我三个讨论问题'];
  return message.suggestedActions?.slice(0, 3) || [];
}

export default function ChatTutor() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [selectedPdf, setSelectedPdf] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const refreshSessions = useCallback(async () => {
    const items = await getChatSessions();
    setSessions(items);
    return items;
  }, []);

  const openSession = useCallback(async (id: string) => {
    setIsHistoryLoading(true);
    try {
      const history = await getChatHistory(id);
      const restored = history.map(historyMessageToChat).filter((item): item is ChatMessage => item !== null);
      setMessages(restored.length > 0 ? restored : [WELCOME_MESSAGE]);
      setSessionId(id);
      window.localStorage.setItem(ACTIVE_SESSION_KEY, id);
      setIsHistoryOpen(false);
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const restore = async () => {
      try {
        const items = await refreshSessions();
        if (cancelled) return;
        const storedId = window.localStorage.getItem(ACTIVE_SESSION_KEY);
        const target = items.find((item) => item.session_id === storedId) || items[0];
        if (target) {
          await openSession(target.session_id);
        }
      } catch {
        if (!cancelled) setMessages([WELCOME_MESSAGE]);
      } finally {
        if (!cancelled) setIsHistoryLoading(false);
      }
    };
    void restore();
    return () => { cancelled = true; };
  }, [openSession, refreshSessions]);

  const startNewSession = useCallback(() => {
    setMessages([WELCOME_MESSAGE]);
    setSessionId(null);
    setInputValue('');
    setSelectedImage(null);
    setSelectedPdf(null);
    setImagePreview(null);
    setAttachmentError(null);
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setIsHistoryOpen(false);
  }, []);

  const handleRenameSession = useCallback(async (session: ChatSessionSummary) => {
    const nextTitle = window.prompt('输入新的会话名称', session.title)?.trim();
    if (!nextTitle || nextTitle === session.title) return;
    await renameChatSession(session.session_id, nextTitle);
    await refreshSessions();
  }, [refreshSessions]);

  const handleDeleteSession = useCallback(async (session: ChatSessionSummary) => {
    if (!window.confirm(`确定删除“${session.title}”吗？删除后无法恢复。`)) return;
    await deleteChatSession(session.session_id);
    const remaining = await refreshSessions();
    if (sessionId === session.session_id) {
      const next = remaining[0];
      if (next) await openSession(next.session_id);
      else startNewSession();
    }
  }, [openSession, refreshSessions, sessionId, startNewSession]);

  const handleImageSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setAttachmentError('请上传 JPG、PNG 或 WebP 格式的图片');
      return;
    }
    if (file.size > MAX_IMAGE_SIZE) {
      setAttachmentError('图片大小不能超过 10MB');
      return;
    }
    setAttachmentError(null);
    setSelectedImage(file);
    setSelectedPdf(null);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handlePdfSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (file.type !== 'application/pdf') {
      setAttachmentError('请上传 PDF 格式的文件');
      return;
    }
    if (file.size > MAX_PDF_SIZE) {
      setAttachmentError('PDF 文件大小不能超过 50MB');
      return;
    }
    setAttachmentError(null);
    setSelectedPdf(file);
    setSelectedImage(null);
    setImagePreview(null);
  }, []);

  const clearAttachments = useCallback(() => {
    setSelectedImage(null);
    setSelectedPdf(null);
    setImagePreview(null);
    setAttachmentError(null);
  }, []);

  const sendMessage = useCallback(async (
    content: string,
    image?: File,
    pdf?: File,
    followup?: { type: 'art' | 'paper'; sessionId: string },
  ) => {
    if (isLoading || (!content.trim() && !image && !pdf)) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: content.trim() || (image ? `上传了图片：${image.name}` : `上传了PDF：${pdf?.name}`),
      timestamp: Date.now() / 1000,
      imageFile: image ? { name: image.name, preview: imagePreview || undefined } : undefined,
      pdfFile: pdf ? { name: pdf.name } : undefined,
    };
    setMessages((previous) => [...previous, userMessage]);
    setIsLoading(true);
    setAttachmentError(null);

    try {
      const response: ChatResponseData = await sendChatMessage({
        session_id: sessionId || undefined,
        message: content,
        image,
        pdf,
        followup_type: followup?.type === 'art' ? 'image' : followup?.type === 'paper' ? 'pdf' : undefined,
        followup_session_id: followup?.sessionId,
      });
      setSessionId(response.session_id);
      window.localStorage.setItem(ACTIVE_SESSION_KEY, response.session_id);
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.reply,
        timestamp: Date.now() / 1000,
        diagnosisResult: response.diagnosis_result,
        interpretResult: response.interpret_result,
        suggestedActions: response.suggested_actions,
      };
      setMessages((previous) => [...previous, assistantMessage]);
      await refreshSessions();
    } catch (err) {
      setMessages((previous) => [...previous, {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: `抱歉，处理时出现了错误：${err instanceof Error ? err.message : '未知错误'}\n\n你的输入已经保留，可以调整后重新发送。`,
        timestamp: Date.now() / 1000,
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [imagePreview, isLoading, refreshSessions, sessionId]);

  const handleSubmit = useCallback(() => {
    const content = inputValue;
    const image = selectedImage || undefined;
    const pdf = selectedPdf || undefined;
    setInputValue('');
    clearAttachments();
    void sendMessage(content, image, pdf);
  }, [clearAttachments, inputValue, selectedImage, selectedPdf, sendMessage]);

  const handleQuickAction = useCallback((
    prompt: string,
    resultType: 'art' | 'paper',
    resultSessionId: string,
  ) => {
    void sendMessage(prompt, undefined, undefined, { type: resultType, sessionId: resultSessionId });
  }, [sendMessage]);

  const handleKnowledgePointClick = useCallback((
    point: KnowledgePoint,
    resultType: 'art' | 'paper',
    resultSessionId?: string,
  ) => {
    if (!resultSessionId) return;
    handleQuickAction(`请详细讲解「${point.name}」：${point.description}`, resultType, resultSessionId);
  }, [handleQuickAction]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const isEmptyConversation = !isHistoryLoading
    && !isLoading
    && messages.length === 1
    && Boolean(messages[0]?.isWelcome);

  const renderComposer = (welcome = false) => (
    <div className={`chat-input-container ${welcome ? 'chat-input-welcome' : ''}`}>
      {attachmentError && <div className="chat-attachment-error" role="alert">{attachmentError}</div>}
      {(selectedImage || selectedPdf) && (
        <div className="chat-attachments-bar">
          {selectedImage && imagePreview && (
            <div className="chat-attachment-chip">
              <img src={imagePreview} alt="" className="chip-thumb" />
              <span className="chip-name">{selectedImage.name}</span>
              <button onClick={clearAttachments} className="chip-remove" type="button" aria-label="移除图片"><X size={14} /></button>
            </div>
          )}
          {selectedPdf && (
            <div className="chat-attachment-chip pdf">
              <FileText size={18} />
              <span className="chip-name">{selectedPdf.name}</span>
              <button onClick={clearAttachments} className="chip-remove" type="button" aria-label="移除PDF"><X size={14} /></button>
            </div>
          )}
        </div>
      )}
      <div className="chat-input-row">
        <div className="chat-input-actions">
          <button type="button" className="chat-action-btn" onClick={() => imageInputRef.current?.click()} aria-label="上传图片" title="上传图片" disabled={isLoading}><ImageIcon size={20} /></button>
          <button type="button" className="chat-action-btn" onClick={() => pdfInputRef.current?.click()} aria-label="上传PDF" title="上传PDF" disabled={isLoading}><FileText size={20} /></button>
        </div>
        <input ref={imageInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImageSelect} className="upload-input" />
        <input ref={pdfInputRef} type="file" accept="application/pdf" onChange={handlePdfSelect} className="upload-input" />
        <textarea className="chat-textarea" placeholder="描述你的作品、问题或阅读目标…" value={inputValue} onChange={(event) => setInputValue(event.target.value)} onKeyDown={handleKeyDown} disabled={isLoading} rows={1} />
        <button type="button" className="chat-send-btn" onClick={handleSubmit} aria-label="发送消息" disabled={isLoading || (!inputValue.trim() && !selectedImage && !selectedPdf)}>
          {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
        </button>
      </div>
    </div>
  );

  const renderMessageContent = (message: ChatMessage) => {
    if (message.isWelcome) return <WelcomePanel composer={isEmptyConversation ? renderComposer(true) : undefined} onSelect={setInputValue} />;
    if (message.diagnosisResult) {
      return (
        <div>
          <p className="chat-text-preview">{message.content}</p>
          <div className="chat-result-container">
            <DiagnosisResult
              result={message.diagnosisResult}
              onKnowledgeClick={(point) => handleKnowledgePointClick(point, 'art', message.diagnosisResult?.session_id)}
              loadingKnowledgePoint={null}
            />
          </div>
        </div>
      );
    }
    if (message.interpretResult) {
      return (
        <div>
          <p className="chat-text-preview">{message.content}</p>
          <div className="chat-result-container">
            <InterpretResult
              result={message.interpretResult}
              onKnowledgeClick={(point) => handleKnowledgePointClick(point, 'paper', message.interpretResult?.session_id)}
              loadingKnowledgePoint={null}
            />
          </div>
        </div>
      );
    }
    if (message.role === 'assistant') return <ChatMarkdown content={message.content} />;
    return <div className="chat-message-text" style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>;
  };

  return (
    <div className="chat-tutor-page">
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="chat-header-icon"><Palette size={28} /></div>
          <div className="chat-header-copy">
            <h1 className="chat-title">EIDOS</h1>
            <p className="chat-subtitle">陪你一起看作品、读论文、聊美学</p>
          </div>
          <button type="button" className="chat-history-toggle" onClick={() => setIsHistoryOpen((open) => !open)} aria-expanded={isHistoryOpen}>
            <Menu size={18} />
            会话记录
          </button>
        </div>
      </div>

      <div className="chat-workspace">
        <aside className={`chat-history-panel ${isHistoryOpen ? 'open' : ''}`} aria-label="历史会话">
          <button type="button" className="chat-new-session" onClick={startNewSession}>
            <PlusCircle size={17} />
            新建对话
          </button>
          <div className="chat-history-title"><History size={15} /> 历史会话</div>
          <div className="chat-session-list">
            {sessions.length === 0 ? <p className="chat-history-empty">还没有保存的会话</p> : sessions.map((session) => (
              <div key={session.session_id} className={`chat-session-item ${sessionId === session.session_id ? 'active' : ''}`}>
                <button type="button" className="chat-session-open" onClick={() => void openSession(session.session_id)}>
                  <strong>{session.title}</strong>
                  <small>{new Date(session.updated_at * 1000).toLocaleString('zh-CN')}</small>
                </button>
                <div className="chat-session-actions">
                  <button type="button" onClick={() => void handleRenameSession(session)} aria-label={`重命名${session.title}`}><Pencil size={13} /></button>
                  <button type="button" onClick={() => void handleDeleteSession(session)} aria-label={`删除${session.title}`}><Trash2 size={13} /></button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <div className={`chat-main-panel ${isEmptyConversation ? 'is-empty' : ''}`}>
          <div className="chat-messages-container">
            <div className="chat-messages">
              {isHistoryLoading ? (
                <div className="chat-history-loading"><Loader2 size={20} className="animate-spin" /> 正在恢复会话...</div>
              ) : messages.map((message) => {
                const actions = actionsForMessage(message);
                const resultType = message.diagnosisResult ? 'art' : message.interpretResult ? 'paper' : null;
                const resultSessionId = message.diagnosisResult?.session_id || message.interpretResult?.session_id;
                return (
                  <div key={message.id} className={`chat-message-wrapper ${message.role} ${message.isError ? 'error' : ''}`}>
                    <div className="chat-message-avatar">{message.role === 'user' ? <UserIcon size={20} /> : <Bot size={20} />}</div>
                    <div className="chat-message-body">
                      {message.imageFile && (
                        <div className="chat-attachment-preview">
                          {message.imageFile.preview && <div className="chat-attachment-thumb"><img src={message.imageFile.preview} alt={message.imageFile.name} /></div>}
                          <span className="chat-attachment-name">{message.imageFile.name}</span>
                        </div>
                      )}
                      {message.pdfFile && (
                        <div className="chat-attachment-preview pdf">
                          <div className="chat-attachment-thumb pdf"><FileText size={24} /></div>
                          <span className="chat-attachment-name">{message.pdfFile.name}</span>
                        </div>
                      )}
                      <div className={`chat-bubble ${message.role}`}>{renderMessageContent(message)}</div>
                      {actions.length > 0 && (
                        <div className="chat-quick-actions" aria-label="快捷追问">
                          <span><Sparkles size={14} /> 接着探索</span>
                          {actions.map((action) => (
                            <button
                              key={action}
                              type="button"
                              onClick={() => {
                                if (resultType && resultSessionId) handleQuickAction(action, resultType, resultSessionId);
                                else void sendMessage(action);
                              }}
                              disabled={isLoading}
                            >
                              {action}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {isLoading && (
                <div className="chat-message-wrapper assistant">
                  <div className="chat-message-avatar"><Bot size={20} /></div>
                  <div className="chat-bubble assistant loading"><div className="typing-indicator"><span /><span /><span /></div></div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {!isEmptyConversation && renderComposer()}
        </div>
      </div>
    </div>
  );
}
