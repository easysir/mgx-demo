'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { PreviewPanel } from '@/components/preview/PreviewPanel';
import { createSession, fetchMessages, listSessions, sendMessage } from '@/lib/api/chat';
import { useAuth } from '@/hooks/useAuth';
import type { Message, Session } from '@/types/chat';

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

  const hasActiveSession = Boolean(sessionId);

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

  const handleSend = async (content: string) => {
    if (!user || !token) {
      router.push('/login');
      return;
    }
    setIsSending(true);
    setError(null);
    try {
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const session = await createSession(token);
        activeSessionId = session.id;
        setSessionId(session.id);
      }
      const turn = await sendMessage(token, activeSessionId, content);
      setMessages((prev) => [...prev, turn.user, ...turn.responses]);
      await loadSessions();
    } catch (err) {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载会话失败');
    } finally {
      setIsSending(false);
    }
  };

  const handleBackHome = () => {
    setSessionId(undefined);
    setMessages([]);
  };

  const recentSessions = useMemo(() => sessions.slice(0, 5), [sessions]);

  return (
    <main className="workspace">
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

      {!hasActiveSession && messages.length === 0 ? (
        <section className="workspace__home">
          <div className="workspace__home-card">
            <h1>告诉 MGX 你想做什么</h1>
            <form className="workspace__home-form" onSubmit={handleHomeSubmit}>
              <textarea
                rows={4}
                placeholder="例如：搭建一个带深色导航和作品集的个人网站..."
                value={homeDraft}
                onChange={(event) => setHomeDraft(event.target.value)}
                disabled={isSending}
              />
              <button type="submit" disabled={isSending}>
                {isSending ? '生成会话中...' : '发送需求'}
              </button>
            </form>
            <div className="workspace__history">
              <div className="workspace__history-header">
                <span>历史会话</span>
                {isLoadingSessions && <small>加载中...</small>}
              </div>
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
            {error && <p className="workspace__error">{error}</p>}
          </div>
        </section>
      ) : (
        <>
          {error && <p className="workspace__error">{error}</p>}
          <section className="workspace__grid">
            <ChatPanel sessionId={sessionId} messages={messages} isSending={isSending} onSend={handleSend} />
            <div className="workspace__right">
              <EditorPanel />
              <PreviewPanel />
            </div>
          </section>
        </>
      )}
    </main>
  );
}
