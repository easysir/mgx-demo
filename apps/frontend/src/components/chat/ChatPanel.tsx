'use client';

import { useState } from 'react';

import type { Message } from '@/types/chat';

interface ChatPanelProps {
  sessionId?: string;
  messages: Message[];
  streamingMessages?: Message[];
  isSending: boolean;
  error?: string | null;
  onSend: (content: string) => Promise<void>;
}

const labelMap: Record<Message['sender'], string> = {
  user: 'You',
  mike: 'Mike',
  agent: 'Agent',
  status: '状态'
};

export function ChatPanel({
  sessionId,
  messages,
  streamingMessages = [],
  isSending,
  error,
  onSend
}: ChatPanelProps) {
  const [draft, setDraft] = useState('');

  const handleSend = async () => {
    const content = draft.trim();
    if (!content) return;
    setDraft('');
    await onSend(content);
  };

  const formatLabel = (message: Message) => {
    if (message.sender === 'user') return labelMap.user;
    if (message.sender === 'status') {
      return `${message.agent ?? 'Agent'} 状态`;
    }
    if (message.sender === 'agent' || message.sender === 'mike') {
      return message.agent ?? labelMap[message.sender];
    }
    return 'Agent';
  };

  const displayMessages = [...messages, ...streamingMessages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <section className="chat-panel">
      <header className="chat-panel__header">
        <div>
          <p className="eyebrow">会话</p>
          <h2>{sessionId ?? '未启动'}</h2>
        </div>
      </header>

      <div className="chat-panel__messages">
        {displayMessages.length === 0 && <p className="chat-panel__empty">尚无消息，发送第一条指令吧。</p>}
        {displayMessages.map((message) => (
          <article
            key={message.id}
            className={`chat-panel__message chat-panel__message--${message.sender}`}
          >
            <header>
              <strong>{formatLabel(message)}</strong>
              <time>
                {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
              </time>
            </header>
            <p>{message.content}</p>
          </article>
        ))}
      </div>

      {error && <p className="chat-panel__error">{error}</p>}
      <div className="chat-panel__input">
        <textarea
          rows={3}
          value={draft}
          placeholder="描述需求或向 Mike @ 提问..."
          onChange={(event) => setDraft(event.target.value)}
          disabled={isSending}
        />
        <div className="chat-panel__input-actions">
          <button type="button" onClick={() => setDraft('')} className="ghost" disabled={isSending}>
            清空
          </button>
          <button type="button" onClick={handleSend} disabled={isSending}>
            {isSending ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </section>
  );
}
