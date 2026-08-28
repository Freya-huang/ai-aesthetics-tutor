import { HelpCircle, Lightbulb } from 'lucide-react';

interface FollowupCardProps {
  question: string;
  knowledgePointName?: string;
  answer: string;
  index: number;
}

export default function FollowupCard({ question, knowledgePointName, answer, index }: FollowupCardProps) {
  return (
    <div className="followup-card" style={{ animationDelay: `${index * 100}ms` }}>
      <div className="followup-card-question">
        <span className="followup-card-q-icon">
          <HelpCircle size={16} />
        </span>
        <div className="followup-card-q-content">
          {knowledgePointName && (
            <span className="followup-card-kp-tag">
              <Lightbulb size={12} />
              {knowledgePointName}
            </span>
          )}
          <p>{question}</p>
        </div>
      </div>
      <div className="followup-card-answer">
        <p>{answer}</p>
      </div>
    </div>
  );
}
