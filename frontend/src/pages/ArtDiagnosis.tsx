import { useState, useRef, useCallback, type ChangeEvent, type DragEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  Image as ImageIcon,
  X,
  Send,
  RefreshCw,
  Sparkles,
  Home,
} from 'lucide-react';
import { archiveReport, diagnoseArt, followupArt } from '@/api';
import type { ArtDiagnosisOutput, KnowledgePoint } from '@/types';
import Loading from '@/components/Loading';
import ErrorMessage from '@/components/ErrorMessage';
import DiagnosisResult from '@/components/DiagnosisResult';
import FollowupCard from '@/components/FollowupCard';

const MAX_IMAGE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_FORMATS = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];

const ARTWORK_TYPES = [
  { label: '请选择作品类型', value: '' },
  { label: '绘画', value: 'painting' },
  { label: '数字艺术', value: 'digital_art' },
  { label: '摄影', value: 'photography' },
  { label: '素描/速写', value: 'sketch' },
  { label: '海报', value: 'poster' },
  { label: 'PPT', value: 'ppt' },
  { label: '其他', value: 'other' },
] as const;

interface FollowupItem {
  id: string;
  question: string;
  knowledgePointName?: string;
  answer: string;
}

type ArtworkTypeValue = '' | 'painting' | 'digital_art' | 'photography' | 'sketch' | 'poster' | 'ppt' | 'other';

export default function ArtDiagnosis() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [artworkType, setArtworkType] = useState<ArtworkTypeValue>('');
  const [artworkTypeLabel, setArtworkTypeLabel] = useState('');
  const [scene, setScene] = useState('');
  const [intent, setIntent] = useState('');
  const [focusPoint, setFocusPoint] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArtDiagnosisOutput | null>(null);
  const [followups, setFollowups] = useState<FollowupItem[]>([]);
  const [loadingKnowledgePoint, setLoadingKnowledgePoint] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (!ACCEPTED_FORMATS.includes(file.type)) {
      return '请上传 JPG、PNG 或 WebP 格式的图片';
    }
    if (file.size > MAX_IMAGE_SIZE) {
      return '图片大小不能超过 10MB';
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
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
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

  const handleRemoveImage = useCallback(() => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (replaceInputRef.current) {
      replaceInputRef.current.value = '';
    }
  }, []);

  const handleArtworkTypeChange = useCallback((e: ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setArtworkType(val as ArtworkTypeValue);
    const option = ARTWORK_TYPES.find((t) => t.value === val);
    setArtworkTypeLabel(option?.label || '');
  }, []);

  const validateForm = useCallback((): string | null => {
    if (!imageFile) {
      return '请先上传作品图片';
    }
    if (!artworkType) {
      return '请选择作品类型';
    }
    return null;
  }, [imageFile, artworkType]);

  const handleSubmit = useCallback(async () => {
    const validationErr = validateForm();
    if (validationErr) {
      setError(validationErr);
      if (!imageFile) {
        fileInputRef.current?.focus();
      } else if (!artworkType) {
        document.getElementById('artwork-type')?.focus();
      }
      return;
    }

    setError(null);
    setIsSubmitting(true);
    setResult(null);
    setFollowups([]);

    try {
      const focusPoints = focusPoint.trim() ? focusPoint.split(/[,，、\s]+/).filter(Boolean) : undefined;
      const diagnosisResult = await diagnoseArt({
        image: imageFile!,
        artwork_type: artworkType || undefined,
        scene: scene.trim() || undefined,
        intent: intent.trim() || undefined,
        focus_points: focusPoints,
      });
      setResult(diagnosisResult);
      try {
        await archiveReport('art', imageFile?.name || '作品诊断报告', diagnosisResult);
      } catch {
        // Archiving should not hide an otherwise successful diagnosis.
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '诊断失败，请稍后重试';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [imageFile, artworkType, scene, intent, focusPoint, validateForm]);

  const handleKnowledgePointClick = useCallback(
    async (point: KnowledgePoint) => {
      if (!result?.session_id || loadingKnowledgePoint) return;

      setLoadingKnowledgePoint(point.name);
      try {
        const followupResult = await followupArt(result.session_id, point.description, point.name);
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
    setImageFile(null);
    setImagePreview(null);
    setArtworkType('');
    setArtworkTypeLabel('');
    setScene('');
    setIntent('');
    setFocusPoint('');
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
    <div className="art-diagnosis-page">
      <div className="page-header">
        <Link to="/" className="page-back-link">
          <ArrowLeft size={18} />
          <span>返回首页</span>
        </Link>
        <div className="page-header-content">
          <div className="page-icon-wrapper">
            <ImageIcon size={32} />
          </div>
          <div>
            <h1 className="page-title">作品诊断</h1>
            <p className="page-subtitle">
              上传艺术作品图片，AI 将从构图、色彩、技法等多个维度提供专业的美学诊断分析
            </p>
          </div>
        </div>
      </div>

      {error && (
        <ErrorMessage
          message={error}
          onRetry={!result && imageFile && artworkType ? handleSubmit : undefined}
        />
      )}

      {!result && !isSubmitting && (
        <div className="diagnosis-form-container">
          <div className="form-section">
            <h2 className="form-section-title">上传作品</h2>

            {!imagePreview ? (
              <label
                className={`upload-area ${isDragging ? 'dragging' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                htmlFor="art-image-input"
              >
                <input
                  ref={fileInputRef}
                  id="art-image-input"
                  type="file"
                  accept="image/jpeg,image/png,image/jpg,image/webp"
                  onChange={handleInputChange}
                  className="upload-input"
                />
                <div className="upload-icon">
                  <Upload size={40} />
                </div>
                <p className="upload-text">
                  <span className="upload-text-primary">点击上传</span> 或拖拽图片到此处
                </p>
                <p className="upload-hint">支持 JPG、PNG、WebP 格式，大小不超过 10MB</p>
              </label>
            ) : (
              <div className="image-preview-wrapper">
                <img src={imagePreview} alt="作品预览" className="image-preview" />
                <button className="image-remove-btn" onClick={handleRemoveImage} type="button" title="更换图片">
                  <X size={18} />
                </button>
                <div className="image-info">
                  <span className="image-name">{imageFile?.name}</span>
                  <label className="image-replace-btn" htmlFor="art-replace-input">
                    <RefreshCw size={14} />
                    <span>更换图片</span>
                  </label>
                  <input
                    ref={replaceInputRef}
                    id="art-replace-input"
                    type="file"
                    accept="image/jpeg,image/png,image/jpg,image/webp"
                    onChange={handleInputChange}
                    className="upload-input-hidden"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="form-section">
            <h2 className="form-section-title">作品信息</h2>

            <div className="form-group">
              <label className="form-label" htmlFor="artwork-type">
                作品类型 <span className="form-required">*</span>
              </label>
              <select
                id="artwork-type"
                className="form-select"
                value={artworkType}
                onChange={handleArtworkTypeChange}
              >
                {ARTWORK_TYPES.map((t) => (
                  <option key={`${t.label}-${t.value}`} value={t.value} disabled={t.value === ''}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="scene">
                使用场景
              </label>
              <input
                id="scene"
                type="text"
                className="form-input"
                placeholder="例如：课堂练习、比赛投稿、商业设计..."
                value={scene}
                onChange={(e) => setScene(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="intent">
                表达意图
              </label>
              <textarea
                id="intent"
                className="form-textarea"
                placeholder="描述你想通过这幅作品传达什么情感、想法或理念..."
                rows={3}
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="focus">
                本轮关注点
              </label>
              <textarea
                id="focus"
                className="form-textarea"
                placeholder="你希望AI重点关注哪些方面？例如：色彩搭配、构图布局、光影处理..."
                rows={2}
                value={focusPoint}
                onChange={(e) => setFocusPoint(e.target.value)}
              />
            </div>

            <button
              className="submit-btn"
              onClick={handleSubmit}
              type="button"
            >
              <Sparkles size={18} />
              <span>开始诊断</span>
            </button>
          </div>
        </div>
      )}

      {isSubmitting && (
        <div className="diagnosis-loading">
          <Loading text="AI 正在分析你的作品，请稍候..." size="large" />
        </div>
      )}

      {result && !isSubmitting && (
        <div className="diagnosis-result-container">
          <div className="result-header">
            <div className="result-header-left">
              <div className="result-artwork-thumb">
                <img src={imagePreview || ''} alt="作品缩略图" />
              </div>
              <div className="result-meta">
                <h2 className="result-title">诊断报告</h2>
                <p className="result-subtitle">
                  {artworkTypeLabel && <span className="result-tag">{artworkTypeLabel}</span>}
                  {scene && <span className="result-meta-text">{scene}</span>}
                </p>
              </div>
            </div>
            <div className="result-header-actions">
              <button className="result-action-btn" onClick={handleReset} type="button">
                <RefreshCw size={16} />
                <span>重新诊断</span>
              </button>
              <Link to="/" className="result-action-btn result-action-btn-primary">
                <Home size={16} />
                <span>返回首页</span>
              </Link>
            </div>
          </div>

          <DiagnosisResult
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
