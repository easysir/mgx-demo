import { useCallback, useEffect, useMemo, useState } from 'react';

import { fetchSandboxPreview } from '@/lib/api/chat';
import { useAuth } from '@/hooks/useAuth';
import type { SandboxPreviewTarget } from '@/types/chat';

interface PreviewPanelProps {
  sessionId?: string;
}

export function PreviewPanel({ sessionId }: PreviewPanelProps) {
  const { token } = useAuth();
  const [targets, setTargets] = useState<SandboxPreviewTarget[]>([]);
  const [activeUrl, setActiveUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const canLoad = Boolean(token && sessionId);

  const refreshPreview = useCallback(async () => {
    if (!canLoad || !token || !sessionId) {
      setTargets([]);
      setActiveUrl(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchSandboxPreview(token, sessionId);
      setTargets(data.previews);
      if (data.previews.length === 0) {
        setActiveUrl(null);
      } else {
        setActiveUrl((prev) => (prev && data.previews.some((target) => target.url === prev) ? prev : data.previews[0].url));
      }
      setLastUpdated(Date.now());
    } catch (err) {
      setTargets([]);
      setActiveUrl(null);
      setError(err instanceof Error ? err.message : '获取预览信息失败');
    } finally {
      setIsLoading(false);
    }
  }, [canLoad, token, sessionId]);

  useEffect(() => {
    setTargets([]);
    setActiveUrl(null);
    setError(null);
    if (canLoad) {
      refreshPreview();
    }
  }, [sessionId, token, canLoad, refreshPreview]);

  useEffect(() => {
    if (!canLoad) return;
    const handle = setInterval(refreshPreview, 10000);
    return () => clearInterval(handle);
  }, [canLoad, refreshPreview]);

  const statusText = useMemo(() => {
    if (!canLoad) {
      return '请选择一个会话以开启沙箱。';
    }
    if (isLoading) return '刷新预览中...';
    if (error) return error;
    if (!targets.length) {
      return '沙箱已就绪，但未检测到对外暴露的 dev server。请在会话中运行 npm/yarn dev（确保 --host 0.0.0.0）。';
    }
    if (!activeUrl) {
      return '请选择要查看的端口。';
    }
    if (lastUpdated) {
      return `最近更新：${new Date(lastUpdated).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })}`;
    }
    return '';
  }, [canLoad, isLoading, error, targets.length, activeUrl, lastUpdated]);

  return (
    <section className="preview-panel">
      <header>
        <div className="preview-panel__actions">
          {targets.length > 1 && (
            <div className="preview-panel__target-tabs preview-panel__target-tabs--inline">
              {targets.map((target) => (
                <button
                  key={target.container_port}
                  type="button"
                  className={target.url === activeUrl ? 'active' : ''}
                  onClick={() => setActiveUrl(target.url)}
                >
                  Port {target.container_port} → {target.host_port}
                </button>
              ))}
            </div>
          )}
          <button type="button" onClick={refreshPreview} disabled={!canLoad || isLoading}>
            {isLoading ? '刷新中...' : '刷新'}
          </button>
          {activeUrl && (
            <a className="primary" href={activeUrl} target="_blank" rel="noreferrer">
              新窗口打开
            </a>
          )}
        </div>
      </header>

      <div className="preview-panel__frame">
        <div className="preview-panel__screen">
          {/* {!sessionId && <p>选择或创建会话以启动沙箱。</p>}
          {sessionId && statusText && <p className="preview-panel__status">{statusText}</p>} */}
          {activeUrl ? (
            <iframe key={activeUrl} src={activeUrl} title="Sandbox Preview" allow="accelerometer; clipboard-read; clipboard-write; encrypted-media; gyroscope; picture-in-picture" />
          ) : (
            <div className="preview-panel__empty">
              <h3>等待 dev server...</h3>
              <p>请确保在沙箱中运行 `npm run dev -- --host 0.0.0.0 --port 4173` 或其他会暴露端口的命令。</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
