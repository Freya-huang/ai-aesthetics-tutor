import { Link } from 'react-router-dom';
import { Home, SearchX } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="not-found-page">
      <SearchX size={56} />
      <span className="not-found-code">404</span>
      <h1>没有找到这个页面</h1>
      <p>地址可能已经更改，或者输入时多了一个字符。</p>
      <Link to="/" className="result-action-btn result-action-btn-primary">
        <Home size={18} />
        返回首页
      </Link>
    </div>
  );
}
