import { Link } from 'react-router-dom';
import { Image, FileText, ArrowRight, Palette, Sparkles, Compass, BookOpen, Eye, Brain } from 'lucide-react';

export default function Home() {
  const tasks = [
    {
      path: '/art-diagnosis',
      icon: Image,
      title: '作品诊断',
      description: '上传你的艺术作品，获得专业的美学分析与改进建议',
      features: [
        { icon: Eye, text: '构图分析' },
        { icon: Palette, text: '色彩评价' },
        { icon: Compass, text: '技法诊断' },
        { icon: Sparkles, text: '知识拓展' },
      ],
      gradient: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
      bgClass: 'task-card-indigo',
    },
    {
      path: '/paper-interpret',
      icon: FileText,
      title: '论文解读',
      description: '上传美学相关论文PDF，获取深度解读与知识点梳理',
      features: [
        { icon: BookOpen, text: '核心论点' },
        { icon: Brain, text: '方法论解析' },
        { icon: Compass, text: '批判思考' },
        { icon: Sparkles, text: '文献溯源' },
      ],
      gradient: 'linear-gradient(135deg, #9a413b, #c9822c)',
      bgClass: 'task-card-rose',
    },
  ];

  return (
    <div className="home-page">
      <div className="home-hero">
        <div className="home-hero-badge">
          <Sparkles size={16} />
          <span>基于知识库的智能美学教育</span>
        </div>
        <h1 className="home-hero-title">EIDOS</h1>
        <p className="home-hero-subtitle">
          融合人工智能与美学理论，为你的艺术创作与学术研究提供智能辅助
        </p>
      </div>

      <div className="home-tasks">
        {tasks.map((task) => {
          const TaskIcon = task.icon;
          return (
            <Link key={task.path} to={task.path} className={`task-card ${task.bgClass}`}>
              <div className="task-card-icon-wrapper" style={{ background: task.gradient }}>
                <TaskIcon size={32} className="task-card-main-icon" />
              </div>
              <h2 className="task-card-title">{task.title}</h2>
              <p className="task-card-description">{task.description}</p>
              <ul className="task-card-features">
                {task.features.map((feature) => {
                  const FeatureIcon = feature.icon;
                  return (
                    <li key={feature.text}>
                      <FeatureIcon size={14} />
                      <span>{feature.text}</span>
                    </li>
                  );
                })}
              </ul>
              <div className="task-card-action">
                <span>开始使用</span>
                <ArrowRight size={18} className="task-card-arrow" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
