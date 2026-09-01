import { useState, useRef, useCallback, type ChangeEvent, type DragEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  FileText,
  X,
  Send,
  RefreshCw,
  Sparkles,
  Home,
} from 'lucide-react';
import { archiveReport, interpretPaper, followupPaper } from '@/api';
import type { PaperInterpretOutput, KnowledgePoint } from '@/types';
import Loading from '@/components/Loading';
import ErrorMessage from '@/components/ErrorMessage';
import InterpretResult from '@/components/InterpretResult';
import FollowupCard from '@/components/FollowupCard';

const MAX_PDF_SIZE = 50 * 1024 * 1024;
const ACCEPTED_FORMAT = 'application/pdf';

interface FollowupItem {
  id: string;
  question: string;
  knowledgePointName?: string;
  answer: string;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export default function PaperInterpret() {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [readingPurpose, setReadingPurpose] = useState('');
  const [focusQuestions, setFocusQuestions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PaperInterpretOutput | null>(null);
  const [followups, setFollowups] = useState<FollowupItem[]>([]);
  const [loadingKnowledgePoint, setLoadingKnowledgePoint] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (file.type !== ACCEPTED_FORMAT) {
      return '请上传 PDF 格式的文件';
    }
    if (file.size > MAX_PDF_SIZE) {
      return 'PDF 文件大小不能超过 50MB';
    }
    return null;
  }, []);

  const handleFileSelect = useCallback(
    (file: File) => {
      const err = validateFile(file);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      setPdfFile(file);
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLLabelElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleRemovePdf = useCallback(() => {
    setPdfFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (replaceInputRef.current) {
      replaceInputRef.current.value = '';
    }
  }, []);

  const validateForm = useCallback((): string | null => {
    if (!pdfFile) {
      return '请先上传论文PDF文件';
    }
    if (!readingPurpose.trim()) {
      return '请填写阅读目的';
    }
    return null;
  }, [pdfFile, readingPurpose]);

  const handleSubmit = useCallback(async () => {
    const validationErr = validateForm();
    if (validationErr) {
      setError(validationErr);
      if (!pdfFile) {
        fileInputRef.current?.focus();
      } else if (!readingPurpose.trim()) {
        document.getElementById('reading-purpose')?.focus();
      }
      return;
    }

    setError(null);
    setIsSubmitting(true);
    setResult(null);
    setFollowups([]);

    try {
      const focusQ = focusQuestions.trim() ? focusQuestions.split(/[,，、\n]+/).filter(Boolean) : undefined;
      const interpretResult = await interpretPaper({
        pdf_file: pdfFile!,
        reading_purpose: readingPurpose.trim(),
        focus_questions: focusQ,
      });
      setResult(interpretResult);
      try {
        await archiveReport('paper', pdfFile?.name || '论文解读报告', interpretResult);
      } catch {
        // Archiving should not hide an otherwise successful interpretation.
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '解读失败，请稍后重试';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [pdfFile, readingPurpose, focusQuestions, validateForm]);

  const handleKnowledgePointClick = useCallback(
    async (point: KnowledgePoint) => {
      if (!result?.session_id || loadingKnowledgePoint) return;

      setLoadingKnowledgePoint(point.name);
      try {
        const followupResult = await followupPaper(result.session_id, point.description);
        const newFollowup: FollowupItem = {
          id: `${Date.now()}-${point.name}`,
          question: `请详细讲解「${point.name}」：${point.description}`,
          knowledgePointName: point.name,
          answer: followupResult.answer,
        };
        setFollowups((prev) => [...prev, newFollowup]);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : '追问失败，请稍后重试';
        setError(message);
      } finally {
        setLoadingKnowledgePoint(null);
      }
    },
    [result, loadingKnowledgePoint]
  );

  const handleReset = useCallback(() => {
    setPdfFile(null);
    setReadingPurpose('');
    setFocusQuestions('');
    setResult(null);
    setFollowups([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (replaceInputRef.current) {
      replaceInputRef.current.value = '';
    }
  }, []);

  return (
    <div className="paper-interpret-page">
      <div className="page-header">
        <Link to="/" className="page-back-link">
          <ArrowLeft size={18} />
          <span>返回首页</span>
        </Link>
        <div className="page-header-content">
          <div className="page-icon-wrapper">
            <FileText size={32} />
          </div>
          <div>
            <h1 className="page-title">论文解读</h1>
            <p className="page-subtitle">
              上传美学领域学术论文PDF，AI 将为你深度解读核心观点、论证结构与关键概念
            </p>
          </div>
        </div>
      </div>

      {error && (
        <ErrorMessage
          message={error}
          onRetry={!result && pdfFile && readingPurpose.trim() ? handleSubmit : undefined}
        />
      )}

      {!result && !isSubmitting && (
        <div className="interpret-form-container">
          <div className="form-section">
            <h2 className="form-section-title">上传论文</h2>

            {!pdfFile ? (
              <label
                className={`upload-area upload-area-pdf ${isDragging ? 'dragging' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                htmlFor="paper-pdf-input"
              >
                <input
                  ref={fileInputRef}
                  id="paper-pdf-input"
                  type="file"
                  accept="application/pdf"
                  onChange={handleInputChange}
                  className="upload-input"
                />
                <div className="upload-icon upload-icon-pdf">
                  <Upload size={40} />
                </div>
                <p className="upload-text">
                  <span className="upload-text-primary">点击上传</span> 或拖拽PDF到此处
                </p>
                <p className="upload-hint">支持 PDF 格式，大小不超过 50MB</p>
              </label>
            ) : (
              <div className="pdf-preview-wrapper">
                <div className="pdf-preview-card">
                  <div className="pdf-icon">
                    <FileText size={40} />
                  </div>
                  <div className="pdf-info">
                    <span className="pdf-name">{pdfFile.name}</span>
                    <span className="pdf-size">{formatFileSize(pdfFile.size)}</span>
                  </div>
                  <button className="pdf-remove-btn" onClick={handleRemovePdf} type="button" title="移除文件">
                    <X size={18} />
                  </button>
                </div>
                <label className="pdf-replace-btn" htmlFor="paper-replace-input">
                  <RefreshCw size={14} />
                  <span>更换文件</span>
                </label>
                <input
                  ref={replaceInputRef}
                  id="paper-replace-input"
                  type="file"
                  accept="application/pdf"
                  onChange={handleInputChange}
                  className="upload-input-hidden"
                />
              </div>
            )}
          </div>

          <div className="form-section">
            <h2 className="form-section-title">阅读需求</h2>

            <div className="form-group">
              <label className="form-label" htmlFor="reading-purpose">
                阅读目的 <span className="form-required">*</span>
              </label>
              <textarea
                id="reading-purpose"
                className="form-textarea"
                placeholder="描述你为什么要阅读这篇论文，希望获得什么信息或解决什么问题..."
                rows={3}
                value={readingPurpose}
                onChange={(e) => setReadingPurpose(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="focus-questions">
                关注问题
              </label>
              <textarea
                id="focus-questions"
                className="form-textarea"
                placeholder="你特别希望AI关注哪些问题？可以用逗号或换行分隔多个问题（可选）..."
                rows={3}
                value={focusQuestions}
                onChange={(e) => setFocusQuestions(e.target.value)}
              />
            </div>

            <button
              className="submit-btn submit-btn-interpret"
              onClick={handleSubmit}
              type="button"
            >
              <Sparkles size={18} />
              <span>开始解读</span>
            </button>
          </div>
        </div>
      )}

      {isSubmitting && (
        <div className="interpret-loading">
          <Loading text="AI 正在深度解读你的论文，请稍候..." size="large" />
        </div>
      )}

      {result && !isSubmitting && (
        <div className="interpret-result-container">
          <div className="result-header">
            <div className="result-header-left">
              <div className="result-pdf-thumb">
                <FileText size={28} />
              </div>
              <div className="result-meta">
                <h2 className="result-title">论文解读报告</h2>
                <p className="result-subtitle">
                  <span className="result-tag">PDF</span>
                  {pdfFile && <span className="result-meta-text">{pdfFile.name}</span>}
                </p>
              </div>
            </div>
            <div className="result-header-actions">
              <button className="result-action-btn" onClick={handleReset} type="button">
                <RefreshCw size={16} />
                <span>重新解读</span>
              </button>
              <Link to="/" className="result-action-btn result-action-btn-primary">
                <Home size={16} />
                <span>返回首页</span>
              </Link>
            </div>
          </div>

          <InterpretResult
            result={result}
            onKnowledgeClick={handleKnowledgePointClick}
            loadingKnowledgePoint={loadingKnowledgePoint}
          />

          {followups.length > 0 && (
            <div className="followups-section">
              <h3 className="followups-title">
                <Send size={18} />
                <span>追问记录</span>
              </h3>
              <div className="followups-list">
                {followups.map((item, idx) => (
                  <FollowupCard
                    key={item.id}
                    question={item.question}
                    knowledgePointName={item.knowledgePointName}
                    answer={item.answer}
                    index={idx}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
