const devices = ['Desktop', 'Tablet', 'Mobile'];

export function PreviewPanel() {
  return (
    <section className="preview-panel">
      <header>
        <div>
          <p className="eyebrow">预览 / Deploy</p>
          <h2>Live Preview</h2>
        </div>
        <div className="preview-panel__actions">
          {devices.map((device) => (
            <button key={device}>{device}</button>
          ))}
          <button className="primary">部署</button>
        </div>
      </header>

      <div className="preview-panel__frame">
        <div className="preview-panel__frame-bar">
          <span />
          <span />
          <span />
        </div>
        <div className="preview-panel__screen">
          <p>Live Preview</p>
          <h3>最小可用版本</h3>
          <p>右侧区域用于展示实时渲染的站点。后续会接入 Preview Server + nginx 反代。</p>
        </div>
      </div>
    </section>
  );
}

