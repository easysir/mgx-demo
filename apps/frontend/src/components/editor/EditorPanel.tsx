const files = [
  { path: 'pages/index.tsx', status: 'modified' },
  { path: 'components/Hero.tsx', status: 'added' },
  { path: 'styles/global.css', status: 'synced' },
  { path: 'agents/plan.md', status: 'review' }
];

const sampleCode = `export default function HeroSection() {
  return (
    <section className="hero">
      <div className="hero__badge">MGX Workspace</div>
      <h1>AI 团队，帮你 10x 完成前端迭代</h1>
      <p>一句话描述目标，Mike 带队完成需求分析、架构设计、编码和预览。</p>
      <button>立即开始</button>
    </section>
  );
}`;

export function EditorPanel() {
  return (
    <section className="editor-panel">
      <header className="editor-panel__header">
        <div>
          <p className="eyebrow">文件 / 代码</p>
          <h2>Editor + Terminal</h2>
        </div>
        <div className="editor-panel__tabs">
          <button className="active">pages/index.tsx</button>
          <button>app/layout.tsx</button>
          <button>tailwind.config.ts</button>
        </div>
      </header>

      <div className="editor-panel__body">
        <aside>
          <p className="editor-panel__section-title">文件树</p>
          <ul>
            {files.map((file) => (
              <li key={file.path}>
                <span>{file.path}</span>
                <small>{file.status}</small>
              </li>
            ))}
          </ul>
        </aside>

        <div className="editor-panel__code">
          <pre>
            <code>{sampleCode}</code>
          </pre>
        </div>
      </div>

      <footer className="editor-panel__footer">
        <div>
          <p className="editor-panel__section-title">终端</p>
          <code>npm run dev · port 3000</code>
        </div>
        <button type="button">打开终端</button>
      </footer>
    </section>
  );
}

