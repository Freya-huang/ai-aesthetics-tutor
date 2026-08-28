import {
  Target,
  Eye,
  ThumbsUp,
  GraduationCap,
  BookOpen,
  Layers,
  ClipboardList,
  HelpCircle,
  ShieldAlert,
  Library,
} from 'lucide-react';
import type { ArtDiagnosisOutput, KnowledgePoint } from '@/types';
import SourceCard from './SourceCard';
import KnowledgePointTag from './KnowledgePointTag';

interface DiagnosisResultProps {
  result: ArtDiagnosisOutput;
  onKnowledgeClick: (point: KnowledgePoint) => void;
  loadingKnowledgePoint?: string | null;
}

interface SectionConfig {
  key: keyof Omit<ArtDiagnosisOutput, 'sources' | 'recommended_knowledge' | 'session_id'>;
  title: string;
  icon: typeof Target;
  type: 'text' | 'list';
  color: string;
  bgColor: string;
}

const sections: SectionConfig[] = [
  { key: 'creative_goal', title: '你的创作目标', icon: Target, type: 'text', color: '#4f46e5', bgColor: 'rgba(79, 70, 229, 0.08)' },
  { key: 'visual_observations', title: '我观察到的视觉现象', icon: Eye, type: 'text', color: '#0ea5e9', bgColor: 'rgba(14, 165, 233, 0.08)' },
  { key: 'strengths', title: '值得保留的地方', icon: ThumbsUp, type: 'list', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.08)' },
  { key: 'key_learning', title: '本次重点学习', icon: GraduationCap, type: 'text', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.08)' },
  { key: 'aesthetics_knowledge', title: '美学知识讲解', icon: BookOpen, type: 'text', color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.08)' },
  { key: 'multiple_perspectives', title: '多元理解方向', icon: Layers, type: 'list', color: '#ec4899', bgColor: 'rgba(236, 72, 153, 0.08)' },
  { key: 'revision_tasks', title: '本轮修改任务', icon: ClipboardList, type: 'list', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.08)' },
  { key: 'reflection_questions', title: '修改后的反思问题', icon: HelpCircle, type: 'list', color: '#6366f1', bgColor: 'rgba(99, 102, 241, 0.08)' },
  { key: 'usage_boundaries', title: '使用边界', icon: ShieldAlert, type: 'text', color: '#64748b', bgColor: 'rgba(100, 116, 139, 0.08)' },
];

export default function DiagnosisResult({ result, onKnowledgeClick, loadingKnowledgePoint }: DiagnosisResultProps) {
  const renderContent = (section: SectionConfig) => {
    if (section.type === 'list') {
      const items = result[section.key] as string[];
      if (!items || items.length === 0) {
        return <p className="diagnosis-section-empty">暂无内容</p>;
      }
      return (
        <ul className="diagnosis-list">
          {items.map((item, index) => (
            <li key={index} className="diagnosis-list-item">
              <span className="diagnosis-list-bullet" style={{ backgroundColor: section.color }} />
              <span>{item.replace(/^[-•*]\s*/, '')}</span>
            </li>
          ))}
        </ul>
      );
    }
    const text = result[section.key] as string;
    if (!text) {
      return <p className="diagnosis-section-empty">暂无内容</p>;
    }
    return <p className="diagnosis-text">{text}</p>;
  };

  return (
    <div className="diagnosis-result">
      {sections.map((section) => {
        const Icon = section.icon;
        return (
          <div key={section.key} className="diagnosis-section">
            <div className="diagnosis-section-header">
              <span
                className="diagnosis-section-icon"
                style={{ backgroundColor: section.bgColor, color: section.color }}
              >
                <Icon size={18} />
              </span>
              <h3 className="diagnosis-section-title">{section.title}</h3>
            </div>
            <div className="diagnosis-section-body">{renderContent(section)}</div>
          </div>
        );
      })}

      {result.sources && result.sources.length > 0 && (
        <div className="diagnosis-section">
          <div className="diagnosis-section-header">
            <span
              className="diagnosis-section-icon"
              style={{ backgroundColor: 'rgba(100, 116, 139, 0.08)', color: '#64748b' }}
            >
              <Library size={18} />
            </span>
            <h3 className="diagnosis-section-title">知识来源</h3>
          </div>
          <div className="diagnosis-section-body">
            <div className="diagnosis-sources-grid">
              {result.sources.map((source) => (
                <SourceCard key={source.source_id} source={source} />
              ))}
            </div>
          </div>
        </div>
      )}

      {result.recommended_knowledge && result.recommended_knowledge.length > 0 && (
        <div className="diagnosis-section">
          <div className="diagnosis-section-header">
            <span
              className="diagnosis-section-icon"
              style={{ backgroundColor: 'rgba(79, 70, 229, 0.08)', color: '#4f46e5' }}
            >
              <GraduationCap size={18} />
            </span>
            <h3 className="diagnosis-section-title">推荐知识点</h3>
            <span className="diagnosis-section-hint">点击可追问了解更多</span>
          </div>
          <div className="diagnosis-section-body">
            <div className="diagnosis-knowledge-tags">
              {result.recommended_knowledge.map((point) => {
                const isLoading = loadingKnowledgePoint === point.name;
                return (
                  <div key={point.name} className="diagnosis-knowledge-tag-wrapper">
                    {isLoading ? (
                      <span className="knowledge-point-tag knowledge-loading">
                        <span className="knowledge-loading-spinner" />
                        <span>正在获取关于"{point.name}"的解答...</span>
                      </span>
                    ) : (
                      <KnowledgePointTag point={point} onClick={onKnowledgeClick} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
