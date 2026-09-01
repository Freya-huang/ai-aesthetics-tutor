import { Link, useLocation } from 'react-router-dom';
import { Aperture, MessageCircle, Image, FileText, Archive, User } from 'lucide-react';
import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const isChatPage = location.pathname === '/' || location.pathname === '/chat';

  const navItems = [
    { path: '/', label: '对话', icon: MessageCircle },
    { path: '/art-diagnosis', label: '作品诊断', icon: Image },
    { path: '/paper-interpret', label: '论文解读', icon: FileText },
    { path: '/archive', label: '学习档案', icon: Archive },
  ];

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/' || location.pathname === '/chat';
    return location.pathname === path;
  };

  return (
    <div className={`layout ${isChatPage ? 'layout-chat' : ''}`}>
      <header className="layout-header">
        <div className="layout-header-inner">
          <Link to="/" className="layout-logo">
            <span className="layout-logo-icon">
              <Aperture size={24} strokeWidth={1.6} />
            </span>
            <span className="layout-logo-text">EIDOS</span>
          </Link>
          <nav className="layout-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`layout-nav-link ${active ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
          <div className="layout-user">
            <button type="button" className="layout-user-btn" aria-label="个人中心">
              <User size={18} strokeWidth={1.8} />
            </button>
          </div>
        </div>
      </header>
      <main className="layout-main">{children}</main>
      <footer className="layout-footer">
        <p>EIDOS｜智能美学学习辅助系统</p>
      </footer>
    </div>
  );
}
