import { Lightbulb, ChevronRight } from 'lucide-react';
import type { KnowledgePoint } from '@/types';

interface KnowledgePointTagProps {
  point: KnowledgePoint;
  onClick?: (point: KnowledgePoint) => void;
  selected?: boolean;
}

export default function KnowledgePointTag({ point, onClick, selected = false }: KnowledgePointTagProps) {
  const isClickable = !!onClick;

  return (
    <button
      className={`knowledge-point-tag ${selected ? 'selected' : ''} ${isClickable ? 'clickable' : ''}`}
      onClick={() => onClick?.(point)}
      type="button"
      disabled={!isClickable}
    >
      <Lightbulb size={14} />
      <span className="knowledge-point-tag-name">{point.name}</span>
      {isClickable && <ChevronRight size={14} className="knowledge-point-tag-arrow" />}
    </button>
  );
}
