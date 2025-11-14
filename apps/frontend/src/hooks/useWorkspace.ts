'use client';

import { useRouter } from 'next/navigation';
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';

import { API_BASE, createSession, deleteSession, fetchMessages, listSessions, sendMessage } from '@/lib/api/chat';
import { useAuth } from '@/hooks/useAuth';
import type { Message, SenderRole, Session, StreamEvent } from '@/types/chat';

interface UseWorkspaceResult {
  user: ReturnType<typeof useAuth>['user'];
  logout: ReturnType<typeof useAuth>['logout'];
  sessionId: string | undefined;
  sessions: Session[];
  messages: Message[];
  streamingMessages: Message[];
  homeDraft: string;
  setHomeDraft: (value: string) => void;
  isSending: boolean;
  isLoadingSessions: boolean;
  error: string | null;
  fileVersion: number;
  isHomeView: boolean;
  handleSend: (content: string) => Promise<void>;
  handleOpenSession: (id: string) => Promise<void>;
  handleDeleteSession: (id: string) => Promise<void>;
  handleHomeSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  handleBackHome: () => void;
}

export function useWorkspace(): UseWorkspaceResult {
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
  const [fileVersion, setFileVersion] = useState(0);

  const isHomeView = !sessionId && messages.length === 0;

  const loadSessions = useCallback(async () => {
    if (!token) {
      setSessions([]);
      return;
    }
    setIsLoadingSessions(true);
    try {
      const data = await listSessions(token);
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
  }, [token, logout, router]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

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

  const handleSend = useCallback(
    async (content: string) => {
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
    },
    [user, token, router, sessionId, mergeMessages, loadSessions]
  );

  const handleHomeSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const content = homeDraft.trim();
      if (!content) return;
      setHomeDraft('');
      await handleSend(content);
    },
    [homeDraft, handleSend]
  );

  const handleOpenSession = useCallback(
    async (id: string) => {
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
    },
    [token, router]
  );

  const handleDeleteSession = useCallback(
    async (id: string) => {
      if (!token) {
        router.push('/login');
        return;
      }
      if (typeof window !== 'undefined') {
        const confirmed = window.confirm('确定删除该会话吗？此操作不可恢复。');
        if (!confirmed) return;
      }
      setError(null);
      try {
        await deleteSession(token, id);
        if (sessionId === id) {
          setSessionId(undefined);
          setMessages([]);
          setStreamingMessages({});
        }
        await loadSessions();
      } catch (err) {
        setError(err instanceof Error ? err.message : '删除会话失败');
      }
    },
    [token, router, sessionId, loadSessions]
  );

  const handleBackHome = useCallback(() => {
    setSessionId(undefined);
    setMessages([]);
    setStreamingMessages({});
    loadSessions();
  }, [loadSessions]);

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

        const messageId = data.message_id ?? '';
        if (!messageId) return;
        const stableMessageId: string = messageId;

        if (data.type === 'tool_call') {
          const eventTimestamp = data.timestamp ? new Date(data.timestamp).toISOString() : new Date().toISOString();
          const content = data.content ?? `[工具调用] ${data.tool ?? ''}`;
          mergeMessages({
            id: messageId,
            session_id: activeSessionId,
            sender: data.sender ?? 'agent',
            agent: data.agent ?? null,
            content,
            timestamp: eventTimestamp
          });
          return;
        }

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
          const previousEntry = prev[stableMessageId] as Message | undefined;
          const inferredSender: SenderRole = data.sender ?? 'agent';
          const inferredTimestamp = previousEntry?.timestamp ?? data.timestamp ?? new Date().toISOString();
          const baseMessage: Message = previousEntry ?? {
            id: stableMessageId,
            session_id: activeSessionId,
            sender: inferredSender,
            agent: data.agent ?? null,
            content: '',
            timestamp: inferredTimestamp
          };

          const updated: Message =
            data.type === 'status'
              ? {
                  ...baseMessage,
                  sender: 'status',
                  agent: data.agent ?? 'Mike',
                  content: data.content ?? ''
                }
              : {
                  ...baseMessage,
                  content: baseMessage.content + (data.content ?? '')
                };

          if (data.final) {
            mergeMessages({
              ...updated,
              timestamp: baseMessage.timestamp
            });
            const nextState = { ...prev };
            delete nextState[stableMessageId];
            return nextState;
          }
          return { ...prev, [stableMessageId]: updated };
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

  const streamingMessagesList = useMemo(() => Object.values(streamingMessages), [streamingMessages]);

  return {
    user,
    logout,
    sessionId,
    sessions,
    messages,
    streamingMessages: streamingMessagesList,
    homeDraft,
    setHomeDraft,
    isSending,
    isLoadingSessions,
    error,
    fileVersion,
    isHomeView,
    handleSend,
    handleOpenSession,
    handleDeleteSession,
    handleHomeSubmit,
    handleBackHome
  };
}
