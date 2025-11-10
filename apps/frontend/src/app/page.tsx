'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { PreviewPanel } from '@/components/preview/PreviewPanel';
import { API_BASE, createSession, fetchMessages, listSessions, sendMessage } from '@/lib/api/chat';
import { useAuth } from '@/hooks/useAuth';
import type { Message, Session, StreamEvent } from '@/types/chat';

export default function Home() {
  const router = useRouter();
  const { user, token, logout } = useAuth();
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [homeDraft, setHomeDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingMessages, setStreamingMessages] = useState<Record<string, Message>>({});
  const [activeRightTab, setActiveRightTab] = useState<'editor' | 'preview'>('editor');
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [fileVersion, setFileVersion] = useState(0);

  const hasActiveSession = Boolean(sessionId);
  const isHomeView = !hasActiveSession && messages.length === 0;

  const loadSessions = async () => {
    if (!token) {
      setSessions([]);
      return;
    }
    setIsLoadingSessions(true);
    try {
      const data = await listSessions(token);
      // 逆序展示最近创建的
      setSessions(data.sort((a, b) => (a.created_at < b.created_at ? 1 : -1)));
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载会话失败';
      setError(message);
      if (message.toLowerCase().includes('token') || message.includes('未授权')) {
        logout();
        router.push('/login');
      }
    } finally {
      setIsLoadingSessions(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [token]);

  const mergeMessages = useCallback((incoming: Message | Message[]) => {
    const items = Array.isArray(incoming) ? incoming : [incoming];
    setMessages((prev) => {
      const next = [...prev];
      for (const item of items) {
        const index = next.findIndex((message) => message.id === item.id);
        if (index >= 0) {
          next[index] = item;
        } else {
          next.push(item);
        }
      }
      return next;
    });
  }, []);

  const handleSend = async (content: string) => {
    if (!user || !token) {
      router.push('/login');
      return;
    }
    setIsSending(true);
    setError(null);
    let optimisticId: string | null = null;
    try {
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const session = await createSession(token);
        activeSessionId = session.id;
        setSessionId(session.id);
      }
      optimisticId = `pending-${Date.now()}`;
      const optimisticMessage: Message = {
        id: optimisticId,
        session_id: activeSessionId,
        sender: 'user',
        content,
        timestamp: new Date().toISOString(),
        agent: null
      };
      mergeMessages(optimisticMessage);
      const turn = await sendMessage(token, activeSessionId, content);
      setMessages((prev) => {
        const next = prev.filter((message) => message.id !== optimisticId);
        const upsert = (item: Message) => {
          const index = next.findIndex((message) => message.id === item.id);
          if (index >= 0) {
            next[index] = item;
          } else {
            next.push(item);
          }
        };
        upsert(turn.user);
        turn.responses.forEach(upsert);
        return next;
      });
      await loadSessions();
    } catch (err) {
      if (optimisticId) {
        setMessages((prev) => prev.filter((message) => message.id !== optimisticId));
      }
      setError(err instanceof Error ? err.message : '发送失败，请稍后再试');
    } finally {
      setIsSending(false);
    }
  };

  const handleHomeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const content = homeDraft.trim();
    if (!content) return;
    setHomeDraft('');
    await handleSend(content);
  };

  const handleOpenSession = async (id: string) => {
    if (!token) {
      router.push('/login');
      return;
    }
    setError(null);
    setIsSending(true);
    try {
      const history = await fetchMessages(token, id);
      setSessionId(id);
      setMessages(history);
      setStreamingMessages({});
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载会话失败');
    } finally {
      setIsSending(false);
    }
  };

  const handleBackHome = () => {
    setSessionId(undefined);
    setMessages([]);
    loadSessions();
  };

  const recentSessions = useMemo(() => sessions.slice(0, 5), [sessions]);

  useEffect(() => {
    if (!sessionId) {
      setStreamingMessages({});
      return;
    }
    const activeSessionId = sessionId;
    let socket: WebSocket | null = null;
    let cancelled = false;
    const resolveWsBase = () => {
      const configured = process.env.NEXT_PUBLIC_WS_BASE_URL;
      if (configured) return configured.replace(/\/$/, '');

      try {
        const apiUrl = new URL(API_BASE);
        const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${apiUrl.host}`;
      } catch {
        if (typeof window !== 'undefined') {
          return window.location.origin.replace(/^http/, 'ws');
        }
        return 'ws://127.0.0.1:8000';
      }
    };
    const wsBase = resolveWsBase();
    const url = `${wsBase}/api/ws/sessions/${activeSessionId}`;
    try {
      socket = new WebSocket(url);
    } catch (err) {
      console.error('WebSocket connection failed', err);
      return;
    }

    socket.onmessage = (event) => {
      if (cancelled) return;
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        const effectiveSession = data.session_id ?? activeSessionId;
        if (!effectiveSession || effectiveSession !== activeSessionId) return;
        if (data.type === 'file_change') {
          setFileVersion((prev) => prev + 1);
          return;
        }

        const messageId = data.message_id;
        if (!messageId) return;

        if (data.type === 'message' && data.sender === 'user') {
          return;
        }

        if (data.type === 'error') {
          const errorContent = data.content || 'LLM 调用失败，请稍后重试';
          setError(errorContent);
          setIsSending(false);
          setStreamingMessages({});
          mergeMessages({
            id: messageId,
            session_id: activeSessionId,
            sender: 'status',
            agent: data.agent ?? 'Mike',
            content: errorContent,
            timestamp: new Date().toISOString()
          });
          return;
        }

        setStreamingMessages((prev) => {
          const baseMessage: Message = prev[messageId] ?? {
            id: messageId,
            session_id: activeSessionId,
            sender: data.sender,
            agent: data.agent ?? null,
            content: '',
            timestamp: new Date().toISOString()
          };

          const updated: Message =
            data.type === 'status'
              ? {
                  ...baseMessage,
                  sender: 'status',
                  agent: data.agent ?? 'Mike',
                  content: data.content ?? '',
                  timestamp: new Date().toISOString()
                }
              : {
                  ...baseMessage,
                  content: baseMessage.content + (data.content ?? ''),
                  timestamp: new Date().toISOString()
                };

          if (data.final) {
            mergeMessages({
              ...updated,
              timestamp: new Date().toISOString()
            });
            const { [messageId]: _removed, ...rest } = prev;
            return rest;
          }
          return { ...prev, [messageId]: updated };
        });
      } catch (err) {
        console.error('Failed to parse stream event', err);
      }
    };

    socket.onerror = (event) => {
      console.error('WebSocket error', event);
    };

    return () => {
      cancelled = true;
      setStreamingMessages({});
      socket?.close();
    };
  }, [sessionId, mergeMessages]);

  return (
    <main className={`workspace ${isHomeView ? 'workspace--home' : 'workspace--chat'}`}>
      <header className="workspace__nav">
        <div className="workspace__nav-left">
          <button className="workspace__logo" onClick={handleBackHome}>
            MGX
          </button>
        </div>

        <div className="workspace__nav-right">
          {user ? (
            <div className="workspace__user">
              <div>
                <strong>{user.name}</strong>
                <small>
                  {user.plan} · {user.credits} credits
                </small>
              </div>
              <button type="button" className="ghost" onClick={logout}>
                登出
              </button>
            </div>
          ) : (
            <Link className="ghost" href="/login">
              登录
            </Link>
          )}
        </div>
      </header>

      {isHomeView ? (
        <div className="workspace__home-layout">
                    <aside
            className={`workspace__history-sidebar ${isHistoryOpen ? 'open' : 'collapsed'}`}
            aria-label="历史会话"
          >
            <div className="workspace__history-toggle">
              <div>
                <span>历史会话</span>
                {isLoadingSessions && <small>加载中...</small>}
              </div>
              <button type="button" onClick={() => setIsHistoryOpen((prev) => !prev)}>
                {isHistoryOpen ? '收起' : '展开'}
              </button>
            </div>
            <div className="workspace__history-content">
              {recentSessions.length === 0 ? (
                <p className="workspace__history-empty">还没有会话记录</p>
              ) : (
                <ul className="workspace__history-list">
                  {recentSessions.map((session) => (
                    <li key={session.id}>
                      <div>
                        <strong>{session.title}</strong>
                        <small>{new Date(session.created_at).toLocaleString()}</small>
                      </div>
                      <button type="button" onClick={() => handleOpenSession(session.id)} disabled={isSending}>
                        打开
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
          
          <section className="workspace__home">
            <div className="workspace__home-card">
              {/* <h4>告诉 MGX 你想做什么</h4> */}
              <form className="workspace__home-form" onSubmit={handleHomeSubmit}>
                <div className="workspace__home-input">
                  <textarea
                    rows={6}
                    placeholder="例如：搭建一个带深色导航和作品集的个人网站..."
                    value={homeDraft}
                    onChange={(event) => setHomeDraft(event.target.value)}
                    disabled={isSending}
                  />
                  <button type="submit" className="workspace__home-submit" disabled={isSending}>
                    {isSending ? '生成会话中...' : '确认'}
                  </button>
                </div>
              </form>
              {/* {error && <p className="workspace__error">{error}</p>} */}
            </div>
          </section>
        </div>
      ) : (
        <div className="workspace__chat-layout">
          <aside className="workspace__chat-sidebar">
            <ChatPanel
              sessionId={sessionId}
              messages={messages}
              streamingMessages={Object.values(streamingMessages)}
              isSending={isSending}
              error={error}
              onSend={handleSend}
            />
          </aside>
          <div className="workspace__chat-main">
            <div className="workspace__right">
              <div className="workspace__right-tabs">
                <button
                  type="button"
                  className={activeRightTab === 'editor' ? 'active' : ''}
                  onClick={() => setActiveRightTab('editor')}
                >
                  Editor / Terminal
                </button>
                <button
                  type="button"
                  className={activeRightTab === 'preview' ? 'active' : ''}
                  onClick={() => setActiveRightTab('preview')}
                >
                  Preview
                </button>
              </div>
              <div className="workspace__right-body">
                {activeRightTab === 'editor' ? <EditorPanel sessionId={sessionId} fileVersion={fileVersion} /> : <PreviewPanel />}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
