import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert" aria-live="polite">
      <AlertCircle className="error-message-icon" size={24} />
      <p className="error-message-text">{message}</p>
      {onRetry && (
        <button className="error-message-retry" onClick={onRetry}>
          <RefreshCw size={16} />
          <span>重试</span>
        </button>
      )}
    </div>
  );
}
