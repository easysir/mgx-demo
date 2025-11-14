'use client';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { PreviewPanel } from '@/components/preview/PreviewPanel';
import type { Message } from '@/types/chat';

interface WorkspaceShellProps {
  sessionId?: string;
  messages: Message[];
  streamingMessages: Message[];
  isSending: boolean;
  error: string | null;
  onSend: (content: string) => Promise<void>;
  activeTab: 'editor' | 'preview';
  onTabChange: (tab: 'editor' | 'preview') => void;
  fileVersion: number;
}

export function WorkspaceShell({
  sessionId,
  messages,
  streamingMessages,
  isSending,
  error,
  onSend,
  activeTab,
  onTabChange,
  fileVersion
}: WorkspaceShellProps) {
  return (
    <div className="workspace__chat-layout">
      <aside className="workspace__chat-sidebar">
        <ChatPanel
          sessionId={sessionId}
          messages={messages}
          streamingMessages={streamingMessages}
          isSending={isSending}
          error={error}
          onSend={onSend}
        />
      </aside>
      <div className="workspace__chat-main">
        <div className="workspace__right">
          <div className="workspace__right-tabs">
            <button
              type="button"
              className={activeTab === 'editor' ? 'active' : ''}
              onClick={() => onTabChange('editor')}
            >
              Editor / Terminal
            </button>
            <button
              type="button"
              className={activeTab === 'preview' ? 'active' : ''}
              onClick={() => onTabChange('preview')}
            >
              Preview
            </button>
          </div>
          <div className="workspace__right-body">
            {activeTab === 'editor' ? (
              <EditorPanel sessionId={sessionId} fileVersion={fileVersion} />
            ) : (
              <PreviewPanel sessionId={sessionId} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
