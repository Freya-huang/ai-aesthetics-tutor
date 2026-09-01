import {
  BookOpen,
  ClipboardCheck,
  GitBranch,
  GraduationCap,
  HelpCircle,
  Key,
  Lightbulb,
  Quote,
} from 'lucide-react';
import type { PaperInterpretOutput, KnowledgePoint, PageCitation } from '@/types';
import KnowledgePointTag from './KnowledgePointTag';

interface InterpretResultProps {
  result: PaperInterpretOutput;
  onKnowledgeClick: (point: KnowledgePoint) => void;
  loadingKnowledgePoint?: string | null;
}

function PageCitationTag({ page, label }: { page: number; label?: string }) {
  return <span className="page-citation-tag">{label || `[第${page}页]`}</span>;
}

function renderTextWithCitations(text: string) {
  return text.split(/(\[第\d+(?:-\d+)?页\])/g).map((part, index) => {
    const match = part.match(/\[第(\d+)(?:-\d+)?页\]/);
    if (match) return <PageCitationTag key={index} page={Number(match[1])} label={part} />;
    return <span key={index}>{part}</span>;
  });
}

function renderCitations(citations?: PageCitation[]) {
  if (!citations?.length) return null;
  return (
    <div className="interpret-citations-list">
      {citations.map((citation, index) => (
        <div key={`${citation.page_number}-${index}`} className="interpret-citation-item">
          <PageCitationTag page={citation.page_number} />
          {citation.quote_snippet && <span className="interpret-citation-quote">“{citation.quote_snippet}”</span>}
        </div>
      ))}
    </div>
  );
}

function NumberedList({ items }: { items: string[] }) {
  return (
    <ol className="interpret-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="interpret-list-item">
          <span className="interpret-list-number">{index + 1}</span>
          <span className="interpret-list-text">{renderTextWithCitations(item)}</span>
        </li>
      ))}
    </ol>
  );
}

export default function InterpretResult({ result, onKnowledgeClick, loadingKnowledgePoint }: InterpretResultProps) {
  const summary = result.one_sentence_summary || result.core_thesis || result.literature_info;
  const coreQuestions = result.core_questions?.length ? result.core_questions : result.research_questions || [];
  const coreViewpoints = result.core_viewpoints || [];
  const argumentProcess = result.argument_process?.length
    ? result.argument_process
    : (result.argument_structure || []).map((section) => `${section.section || ''}：${section.summary || ''}`);
  const connections = result.course_creation_connections || [];
  const recommendedReading = result.recommended_reading?.slice(0, 3) || [];

  return (
    <div className="interpret-result">
      {summary && (
        <div className="interpret-section interpret-section-core">
          <div className="interpret-core-thesis">
            <div className="interpret-core-icon"><Lightbulb size={24} /></div>
            <div className="interpret-core-content">
              <div className="interpret-core-label">一句话概括</div>
              <p className="interpret-core-text">{renderTextWithCitations(summary)}</p>
            </div>
          </div>
        </div>
      )}

      {coreQuestions.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><HelpCircle size={18} /></span>
            <h3 className="interpret-section-title">论文试图回答的核心问题</h3>
          </div>
          <div className="interpret-section-body"><NumberedList items={coreQuestions} /></div>
        </section>
      )}

      {coreViewpoints.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><BookOpen size={18} /></span>
            <h3 className="interpret-section-title">已呈现的核心观点</h3>
          </div>
          <div className="interpret-section-body"><NumberedList items={coreViewpoints} /></div>
        </section>
      )}

      {result.key_concepts?.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><Key size={18} /></span>
            <h3 className="interpret-section-title">关键概念解释</h3>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-concepts-grid">
              {result.key_concepts.map((concept, index) => (
                <article key={`${concept.name}-${index}`} className="interpret-concept-card">
                  <div className="interpret-concept-header">
                    <h4 className="interpret-concept-name">{concept.name}</h4>
                    {concept.page_number && <PageCitationTag page={concept.page_number} />}
                  </div>
                  <p className="interpret-concept-desc">{renderTextWithCitations(concept.description)}</p>
                  {renderCitations(concept.citations)}
                </article>
              ))}
            </div>
          </div>
        </section>
      )}

      {argumentProcess.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><GitBranch size={18} /></span>
            <h3 className="interpret-section-title">已呈现的论证过程</h3>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-argument-timeline">
              {argumentProcess.map((step, index) => (
                <div key={`${step}-${index}`} className="interpret-argument-item">
                  <div className="interpret-argument-marker">
                    <div className="interpret-argument-dot" />
                    {index < argumentProcess.length - 1 && <div className="interpret-argument-line" />}
                  </div>
                  <div className="interpret-argument-content">
                    <p className="interpret-argument-summary">{renderTextWithCitations(step)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {result.contributions_limitations && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><ClipboardCheck size={18} /></span>
            <h3 className="interpret-section-title">已呈现内容的贡献与局限</h3>
          </div>
          <div className="interpret-section-body">
            <p className="interpret-text">{renderTextWithCitations(result.contributions_limitations)}</p>
          </div>
        </section>
      )}

      {connections.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><Quote size={18} /></span>
            <h3 className="interpret-section-title">与课程 / 创作的联系</h3>
          </div>
          <div className="interpret-section-body"><NumberedList items={connections} /></div>
        </section>
      )}

      {recommendedReading.length > 0 && (
        <section className="interpret-section">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><GraduationCap size={18} /></span>
            <h3 className="interpret-section-title">推荐延伸阅读</h3>
            <span className="interpret-section-hint">最多3项</span>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-reading-list">
              {recommendedReading.map((point) => (
                <div key={`${point.source_id}-${point.name}`} className="interpret-reading-item">
                  {loadingKnowledgePoint === point.name ? (
                    <span className="knowledge-point-tag knowledge-loading">
                      <span className="knowledge-loading-spinner" />正在获取“{point.name}”的解答...
                    </span>
                  ) : (
                    <KnowledgePointTag point={point} onClick={onKnowledgeClick} />
                  )}
                  {point.description && <p>{point.description}</p>}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {result.next_reflection_task && (
        <section className="interpret-section interpret-reflection-task">
          <div className="interpret-section-header">
            <span className="interpret-section-icon"><Quote size={18} /></span>
            <h3 className="interpret-section-title">下一步反思任务</h3>
          </div>
          <div className="interpret-section-body">
            <p className="interpret-text">{renderTextWithCitations(result.next_reflection_task)}</p>
            <span className="interpret-task-note">先完成判断并说明证据，暂不提供标准答案。</span>
          </div>
        </section>
      )}
    </div>
  );
}
