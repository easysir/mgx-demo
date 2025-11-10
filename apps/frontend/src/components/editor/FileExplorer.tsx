import { useEffect, useState } from 'react';

import type { FileNode } from '@/types/chat';

interface FileExplorerProps {
  tree: FileNode[];
  loading: boolean;
  onRefresh: () => void;
  onSelect: (node: FileNode) => void;
  activePath?: string;
}

function FileNodeItem({ node, depth, onSelect, activePath }: { node: FileNode; depth: number; onSelect: (node: FileNode) => void; activePath?: string }) {
  const [expanded, setExpanded] = useState(depth < 2);

  useEffect(() => {
    if (activePath && activePath.startsWith(node.path)) {
      setExpanded(true);
    }
  }, [activePath, node.path]);

  const isActive = activePath === node.path;
  const paddingLeft = depth * 12;

  const handleClick = () => {
    if (node.type === 'directory') {
      setExpanded((prev) => !prev);
    } else {
      onSelect(node);
    }
  };

  return (
    <li>
      <div className={`file-node ${node.type} ${isActive ? 'active' : ''}`} style={{ paddingLeft }}>
        <button type="button" onClick={handleClick}>
          {node.type === 'directory' ? (expanded ? '📂' : '📁') : '📄'} {node.name || 'workspace'}
        </button>
        {node.type === 'file' && (
          <span className="file-node__meta">{(node.size / 1024).toFixed(1)} KB</span>
        )}
      </div>
      {node.children && node.children.length > 0 && expanded && (
        <ul>
          {node.children.map((child) => (
            <FileNodeItem key={`${node.path}-${child.path}`} node={child} depth={depth + 1} onSelect={onSelect} activePath={activePath} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function FileExplorer({ tree, loading, onRefresh, onSelect, activePath }: FileExplorerProps) {
  return (
    <aside className="file-explorer">
      {/* <div className="file-explorer__header">
        <span>沙箱文件</span>
        <button type="button" onClick={onRefresh} disabled={loading}>
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div> */}
      {tree.length === 0 ? (
        <p className="file-explorer__empty">暂无文件，等待沙箱写入...</p>
      ) : (
        <ul>
          {tree.map((node) => (
            <FileNodeItem key={node.path || 'root'} node={node} depth={0} onSelect={onSelect} activePath={activePath} />
          ))}
        </ul>
      )}
    </aside>
  );
}
