import { Loader2 } from 'lucide-react';

interface LoadingProps {
  text?: string;
  size?: 'small' | 'medium' | 'large';
}

export default function Loading({ text = '加载中...', size = 'medium' }: LoadingProps) {
  const sizeMap = {
    small: 20,
    medium: 36,
    large: 52,
  };

  return (
    <div className={`loading loading-${size}`}>
      <Loader2 className="loading-spinner" size={sizeMap[size]} />
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
}
