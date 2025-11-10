'use client';

import { useEffect, useState } from 'react';

import { fetchFileContent, fetchFileTree } from '@/lib/api/chat';
import { useAuth } from '@/hooks/useAuth';
import type { FileContentResponse, FileNode } from '@/types/chat';

import { FileExplorer } from './FileExplorer';
import { CodePreview } from './CodePreview';

interface EditorPanelProps {
  sessionId?: string;
  fileVersion: number;
}

export function EditorPanel({ sessionId, fileVersion }: EditorPanelProps) {
  const { token } = useAuth();
  const [tree, setTree] = useState<FileNode[]>([]);
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [activeFile, setActiveFile] = useState<FileContentResponse | null>(null);
  const [activePath, setActivePath] = useState<string | null>(null);
  const [isFileLoading, setIsFileLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canLoad = Boolean(token && sessionId);

  const loadTree = async () => {
    if (!canLoad) return;
    setIsTreeLoading(true);
    setError(null);
    try {
      const data = await fetchFileTree(token!, sessionId!, { depth: 3 });
      setTree(data.entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件树失败');
    } finally {
      setIsTreeLoading(false);
    }
  };

  const loadFile = async (path: string) => {
    if (!canLoad) return;
    setIsFileLoading(true);
    setError(null);
    try {
      const file = await fetchFileContent(token!, sessionId!, path);
      setActiveFile(file);
      setActivePath(path);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件失败');
    } finally {
      setIsFileLoading(false);
    }
  };

  useEffect(() => {
    setTree([]);
    setActiveFile(null);
    setActivePath(null);
    if (canLoad) {
      loadTree();
    }
  }, [sessionId, token]);

  useEffect(() => {
    if (!canLoad) return;
    loadTree();
    if (activePath) {
      loadFile(activePath);
    }
  }, [fileVersion]);

  return (
    <section className="editor-panel">
      {/* <header className="editor-panel__header">
        <div>
          <p className="eyebrow">沙箱文件</p>
          <h2>Editor (只读)</h2>
        </div>
        <button type="button" onClick={loadTree} disabled={isTreeLoading || !canLoad}>
          {isTreeLoading ? '刷新中...' : '刷新文件树'}
        </button>
      </header> */}

      {error && <p className="workspace__error">{error}</p>}

      <div className="editor-panel__body">
        <FileExplorer
          tree={tree}
          loading={isTreeLoading}
          onRefresh={loadTree}
          onSelect={(node) => loadFile(node.path)}
          activePath={activePath ?? undefined}
        />
        <div className="editor-panel__code">
          <CodePreview file={activeFile} loading={isFileLoading} />
        </div>
      </div>
    </section>
  );
}
