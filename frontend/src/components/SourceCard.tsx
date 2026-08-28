import { BookOpen, Bookmark, Star, Brain, Eye } from 'lucide-react';
import type { SourceCard as SourceCardType } from '@/types';

interface SourceCardProps {
  source: SourceCardType;
}

const categoryConfig: Record<string, { icon: typeof BookOpen; label: string }> = {
  AIA: { icon: Brain, label: 'AI与艺术' },
  THE: { icon: BookOpen, label: '美学理论' },
  VIS: { icon: Eye, label: '视觉原理' },
  OTHER: { icon: Bookmark, label: '其他' },
};

export default function SourceCard({ source }: SourceCardProps) {
  const config = categoryConfig[source.category] || categoryConfig.OTHER;
  const Icon = config.icon;

  return (
    <div className="source-card">
      <div className="source-card-header">
        <span className="source-card-category">
          <Icon size={14} />
          <span>{config.label}</span>
        </span>
        <span className="source-card-relevance" title={`相关性: ${Math.round(source.relevance * 100)}%`}>
          <Star size={12} fill="currentColor" />
          <span>{Math.round(source.relevance * 100)}%</span>
        </span>
      </div>
      <h4 className="source-card-title">{source.title}</h4>
      <p className="source-card-snippet">"{source.snippet}"</p>
    </div>
  );
}
