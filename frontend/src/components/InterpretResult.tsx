import {
  BookOpen,
  Lightbulb,
  HelpCircle,
  Key,
  GitBranch,
  History,
  Image as ImageIcon,
  ClipboardCheck,
  GraduationCap,
  Quote,
} from 'lucide-react';
import type { PaperInterpretOutput, KnowledgePoint, PageCitation } from '@/types';
import SourceCard from './SourceCard';
import KnowledgePointTag from './KnowledgePointTag';

interface InterpretResultProps {
  result: PaperInterpretOutput;
  onKnowledgeClick: (point: KnowledgePoint) => void;
  loadingKnowledgePoint?: string | null;
}

const PRIMARY_COLOR = '#0d9488';
const PRIMARY_BG = 'rgba(13, 148, 136, 0.08)';
const PRIMARY_LIGHT = '#14b8a6';

function PageCitationTag({ page }: { page: number }) {
  return (
    <span className="page-citation-tag">
      [第{page}页]
    </span>
  );
}

function renderTextWithCitations(text: string) {
  const parts = text.split(/(\[第\d+页\])/g);
  return parts.map((part, idx) => {
    const match = part.match(/\[第(\d+)页\]/);
    if (match) {
      return <PageCitationTag key={idx} page={parseInt(match[1], 10)} />;
    }
    return <span key={idx}>{part}</span>;
  });
}

function renderCitations(citations?: PageCitation[]) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="interpret-citations-list">
      {citations.map((cite, idx) => (
        <div key={idx} className="interpret-citation-item">
          <PageCitationTag page={cite.page_number} />
          {cite.quote_snippet && (
            <span className="interpret-citation-quote">"{cite.quote_snippet}"</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default function InterpretResult({ result, onKnowledgeClick, loadingKnowledgePoint }: InterpretResultProps) {
  const recommendedReading = result.recommended_reading?.slice(0, 3) || [];
  const hasClassicalConnections = result.classical_connections && result.classical_connections.length > 0;
  const hasPaperImages = result.paper_images && result.paper_images.length > 0;
  const pageCitations = result.sources?.page_citations || [];
  const ragSources = result.sources?.rag_sources || [];

  return (
    <div className="interpret-result">
      <div className="interpret-section interpret-section-literature">
        <div className="interpret-section-header">
          <span
            className="interpret-section-icon"
            style={{ backgroundColor: PRIMARY_BG, color: PRIMARY_COLOR }}
          >
            <BookOpen size={18} />
          </span>
          <h3 className="interpret-section-title">文献信息与解析范围</h3>
        </div>
        <div className="interpret-section-body">
          <p className="interpret-text">{result.literature_info}</p>
        </div>
      </div>

      {result.core_thesis && (
        <div className="interpret-section interpret-section-core">
          <div className="interpret-core-thesis">
            <div className="interpret-core-icon">
              <Lightbulb size={24} />
            </div>
            <div className="interpret-core-content">
              <div className="interpret-core-label">一句话核心观点</div>
              <p className="interpret-core-text">{renderTextWithCitations(result.core_thesis)}</p>
            </div>
          </div>
        </div>
      )}

      {result.research_questions && result.research_questions.length > 0 && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: 'rgba(6, 182, 212, 0.08)', color: '#0891b2' }}
            >
              <HelpCircle size={18} />
            </span>
            <h3 className="interpret-section-title">研究问题</h3>
          </div>
          <div className="interpret-section-body">
            <ul className="interpret-list">
              {result.research_questions.map((q, idx) => {
                const pageMatch = q.match(/\[第(\d+)页\]/);
                const page = pageMatch ? parseInt(pageMatch[1], 10) : null;
                const cleanText = q.replace(/\[第\d+页\]/g, '').trim();
                return (
                  <li key={idx} className="interpret-list-item">
                    <span className="interpret-list-number">{idx + 1}</span>
                    <span className="interpret-list-text">{cleanText}</span>
                    {page && <PageCitationTag page={page} />}
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}

      {result.key_concepts && result.key_concepts.length > 0 && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: 'rgba(245, 158, 11, 0.08)', color: '#d97706' }}
            >
              <Key size={18} />
            </span>
            <h3 className="interpret-section-title">关键概念</h3>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-concepts-grid">
              {result.key_concepts.map((concept, idx) => (
                <div key={idx} className="interpret-concept-card">
                  <div className="interpret-concept-header">
                    <h4 className="interpret-concept-name">{concept.name}</h4>
                    {concept.citations && concept.citations.length > 0 && (
                      <div className="interpret-concept-pages">
                        {concept.citations.map((cite, cIdx) => (
                          <PageCitationTag key={cIdx} page={cite.page_number} />
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="interpret-concept-desc">{concept.description}</p>
                  {renderCitations(concept.citations)}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {result.argument_structure && result.argument_structure.length > 0 && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: 'rgba(139, 92, 246, 0.08)', color: '#7c3aed' }}
            >
              <GitBranch size={18} />
            </span>
            <h3 className="interpret-section-title">论证结构</h3>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-argument-timeline">
              {result.argument_structure.map((section, idx) => (
                <div key={idx} className="interpret-argument-item">
                  <div className="interpret-argument-marker">
                    <div className="interpret-argument-dot" />
                    {idx < result.argument_structure.length - 1 && (
                      <div className="interpret-argument-line" />
                    )}
                  </div>
                  <div className="interpret-argument-content">
                    <div className="interpret-argument-header">
                      <h4 className="interpret-argument-section">{section.section}</h4>
                      {section.page && <PageCitationTag page={section.page} />}
                    </div>
                    <p className="interpret-argument-summary">{section.summary}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="interpret-section">
        <div className="interpret-section-header">
          <span
            className="interpret-section-icon"
            style={{ backgroundColor: 'rgba(236, 72, 153, 0.08)', color: '#db2777' }}
          >
            <History size={18} />
          </span>
          <h3 className="interpret-section-title">与经典美学问题的关联</h3>
        </div>
        <div className="interpret-section-body">
          {hasClassicalConnections ? (
            <div className="interpret-connections-list">
              {result.classical_connections.map((conn, idx) => (
                <div key={idx} className="interpret-connection-item">
                  <h4 className="interpret-connection-topic">{conn.topic}</h4>
                  <p className="interpret-connection-text">{conn.connection}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="interpret-section-empty">暂无充分证据支持的概念史关联</p>
          )}
        </div>
      </div>

      {hasPaperImages && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: 'rgba(14, 165, 233, 0.08)', color: '#0284c7' }}
            >
              <ImageIcon size={18} />
            </span>
            <h3 className="interpret-section-title">论文中的图片或案例</h3>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-images-grid">
              {result.paper_images.map((img, idx) => (
                <div key={idx} className="interpret-image-card">
                  <div className="interpret-image-header">
                    <span className="interpret-image-id">{img.image_id}</span>
                    <PageCitationTag page={img.page_number} />
                  </div>
                  {img.description && (
                    <p className="interpret-image-desc">{img.description}</p>
                  )}
                  <div className="interpret-image-observation">
                    <Quote size={14} className="interpret-quote-icon" />
                    <p>{img.observation}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {result.contributions_limitations && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: 'rgba(16, 185, 129, 0.08)', color: '#059669' }}
            >
              <ClipboardCheck size={18} />
            </span>
            <h3 className="interpret-section-title">贡献、局限与待讨论问题</h3>
          </div>
          <div className="interpret-section-body">
            <p className="interpret-text">{renderTextWithCitations(result.contributions_limitations)}</p>
          </div>
        </div>
      )}

      {recommendedReading.length > 0 && (
        <div className="interpret-section">
          <div className="interpret-section-header">
            <span
              className="interpret-section-icon"
              style={{ backgroundColor: PRIMARY_BG, color: PRIMARY_COLOR }}
            >
              <GraduationCap size={18} />
            </span>
            <h3 className="interpret-section-title">建议继续阅读的知识点</h3>
            <span className="interpret-section-hint">点击可追问了解更多（最多3个）</span>
          </div>
          <div className="interpret-section-body">
            <div className="interpret-knowledge-tags">
              {recommendedReading.map((point) => {
                const isLoading = loadingKnowledgePoint === point.name;
                return (
                  <div key={point.name} className="interpret-knowledge-tag-wrapper">
                    {isLoading ? (
                      <span className="knowledge-point-tag knowledge-loading" style={{ borderColor: PRIMARY_LIGHT, background: PRIMARY_BG, color: PRIMARY_COLOR }}>
                        <span className="knowledge-loading-spinner" style={{ borderTopColor: PRIMARY_COLOR }} />
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

      <div className="interpret-section">
        <div className="interpret-section-header">
          <span
            className="interpret-section-icon"
            style={{ backgroundColor: 'rgba(100, 116, 139, 0.08)', color: '#64748b' }}
          >
            <Quote size={18} />
          </span>
          <h3 className="interpret-section-title">来源与使用边界</h3>
        </div>
        <div className="interpret-section-body">
          {pageCitations.length > 0 && (
            <div className="interpret-page-citations">
              <h4 className="interpret-subsection-title">页码引用列表</h4>
              <div className="interpret-page-citations-list">
                {pageCitations.map((cite, idx) => (
                  <div key={idx} className="interpret-page-citation-item">
                    <PageCitationTag page={cite.page_number} />
                    {cite.quote_snippet && (
                      <span className="interpret-citation-snippet">"{cite.quote_snippet}"</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {ragSources.length > 0 && (
            <div className="interpret-rag-sources">
              <h4 className="interpret-subsection-title">RAG知识来源</h4>
              <div className="interpret-sources-grid">
                {ragSources.map((source) => (
                  <SourceCard key={source.source_id} source={source} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
