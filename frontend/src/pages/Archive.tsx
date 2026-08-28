import { useCallback, useEffect, useState } from 'react';
import { Archive as ArchiveIcon, BookOpen, FileText, Image, Leaf, Sprout, TreePine, Trash2 } from 'lucide-react';
import { deleteArchivedReport, listArchivedReports, type ArchivedReport } from '@/api';
import type { ArtDiagnosisOutput, PaperInterpretOutput } from '@/types';
import DiagnosisResult from '@/components/DiagnosisResult';
import InterpretResult from '@/components/InterpretResult';
import Loading from '@/components/Loading';
import ErrorMessage from '@/components/ErrorMessage';

export default function Archive() {
  const [reports, setReports] = useState<ArchivedReport[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await listArchivedReports();
      setReports(items);
      setSelectedId((current) => current && items.some((item) => item.report_id === current)
        ? current
        : items[0]?.report_id || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '学习档案加载失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  const handleDelete = async (report: ArchivedReport) => {
    if (!window.confirm(`确定删除“${report.title}”吗？`)) return;
    try {
      await deleteArchivedReport(report.report_id);
      await loadReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    }
  };

  const selected = reports.find((report) => report.report_id === selectedId) || null;
  const forestTrees = reports.flatMap((report) => {
    const points = report.report_type === 'art'
      ? (report.result as ArtDiagnosisOutput).recommended_knowledge?.map((point) => ({ name: point.name, description: point.description })) || []
      : (report.result as PaperInterpretOutput).key_concepts?.map((point) => ({ name: point.name, description: point.description })) || [];
    const fallback = report.report_type === 'art'
      ? [{ name: '本次重点学习', description: (report.result as ArtDiagnosisOutput).key_learning }]
      : [{ name: '论文核心观点', description: (report.result as PaperInterpretOutput).core_thesis }];

    return (points.length > 0 ? points : fallback).map((point, pointIndex) => ({
      ...point,
      id: `${report.report_id}-${pointIndex}`,
      reportId: report.report_id,
      reportType: report.report_type,
    }));
  });

  const selectTree = (reportId: string) => {
    setSelectedId(reportId);
    window.requestAnimationFrame(() => {
      document.getElementById('archive-report-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  return (
    <div className="archive-page">
      <div className="archive-heading">
        <div className="page-icon-wrapper archive-heading-icon"><ArchiveIcon size={30} /></div>
        <div>
          <h1 className="page-title">学习档案 · 成长森林</h1>
          <p className="page-subtitle">每掌握一个知识点，就在这里种下一棵树。让学习留下可见的生长痕迹。</p>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadReports} />}
      {isLoading ? (
        <Loading text="正在加载学习档案..." size="large" />
      ) : (
        <>
          <section className="growth-forest" aria-labelledby="growth-forest-title">
            <div className="growth-forest-summary">
              <div>
                <span className="growth-forest-kicker"><Leaf size={14} /> YOUR LEARNING LANDSCAPE</span>
                <h2 id="growth-forest-title">一片由知识长成的森林</h2>
                <p>每棵树都对应一块进入学习档案的知识。点击树木，可以回到它生长的那次学习。</p>
              </div>
              <div className="growth-forest-stats" aria-label="成长统计">
                <div><strong>{forestTrees.length}</strong><span>知识树</span></div>
                <div><strong>{reports.length}</strong><span>学习记录</span></div>
              </div>
            </div>

            <div className={`growth-forest-map ${forestTrees.length === 0 ? 'is-empty' : ''}`}>
              <div className="growth-forest-island" aria-hidden="true" />
              {forestTrees.length === 0 ? (
                <div className="growth-forest-empty">
                  <span><Sprout size={30} strokeWidth={1.5} /></span>
                  <strong>等待第一颗种子</strong>
                  <small>完成一次作品诊断或论文解读，就会长出第一棵知识树。</small>
                </div>
              ) : (
                <div className="growth-tree-layer">
                  {forestTrees.map((tree, index) => (
                    <button
                      key={tree.id}
                      type="button"
                      className={`growth-tree growth-tree-${tree.reportType} growth-tree-stage-${index % 3}`}
                      onClick={() => selectTree(tree.reportId)}
                      title={`${tree.name}：${tree.description}`}
                      aria-label={`查看知识点：${tree.name}`}
                    >
                      <span className="growth-tree-icon"><TreePine strokeWidth={1.45} /></span>
                      <span className="growth-tree-label">{tree.name}</span>
                    </button>
                  ))}
                </div>
              )}
              <div className="growth-forest-legend">
                <span><Image size={13} /> 作品观察林</span>
                <span><BookOpen size={13} /> 论文研读林</span>
              </div>
            </div>
          </section>

          {reports.length === 0 ? (
            <div className="archive-empty">
              <Sprout size={42} />
              <h2>从第一次学习开始种树</h2>
              <p>完成一次作品诊断或论文解读后，报告会自动归档，知识也会在森林里生长。</p>
            </div>
          ) : (
            <div className="archive-layout">
              <aside className="archive-list" aria-label="报告列表">
                {reports.map((report) => {
                  const Icon = report.report_type === 'art' ? Image : FileText;
                  return (
                    <div key={report.report_id} className={`archive-list-item ${selectedId === report.report_id ? 'active' : ''}`}>
                      <button type="button" className="archive-select" onClick={() => setSelectedId(report.report_id)}>
                        <span className={`archive-type-icon ${report.report_type}`}><Icon size={18} /></span>
                        <span className="archive-item-copy">
                          <strong>{report.title}</strong>
                          <small>{report.report_type === 'art' ? '作品诊断' : '论文解读'} · {new Date(report.created_at * 1000).toLocaleString('zh-CN')}</small>
                        </span>
                      </button>
                      <button type="button" className="archive-delete" onClick={() => void handleDelete(report)} aria-label={`删除${report.title}`}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  );
                })}
              </aside>

              <section id="archive-report-detail" className="archive-detail" aria-live="polite">
                {selected?.report_type === 'art' ? (
                  <DiagnosisResult
                    result={selected.result as ArtDiagnosisOutput}
                    onKnowledgeClick={() => undefined}
                  />
                ) : selected ? (
                  <InterpretResult
                    result={selected.result as PaperInterpretOutput}
                    onKnowledgeClick={() => undefined}
                  />
                ) : null}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  );
}
