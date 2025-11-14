'use client';

import type { Session } from '@/types/chat';

interface SessionListPanelProps {
  sessions: Session[];
  isLoading: boolean;
  isBusy: boolean;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}

export function SessionListPanel({ sessions, isLoading, isBusy, onOpen, onDelete }: SessionListPanelProps) {
  return (
    <aside className="workspace__history-sidebar" aria-label="历史会话">
      <div className="workspace__history-toggle">
        <div>
          <span>历史会话</span>
          {isLoading && <small>加载中...</small>}
        </div>
      </div>
      <div className="workspace__history-content">
        {sessions.length === 0 ? (
          <p className="workspace__history-empty">还没有会话记录</p>
        ) : (
          <ul className="workspace__history-list">
            {sessions.map((session) => (
              <li key={session.id}>
                <div>
                  <strong>{session.title}</strong>
                  <small>{new Date(session.created_at).toLocaleString()}</small>
                </div>
                <div className="workspace__history-actions">
                  <button type="button" onClick={() => onOpen(session.id)} disabled={isBusy}>
                    打开
                  </button>
                  <button type="button" className="ghost" onClick={() => onDelete(session.id)} disabled={isBusy}>
                    删除
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
