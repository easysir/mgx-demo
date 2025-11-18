"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createSession,
  deleteSession,
  fetchMessages,
  listSessions,
  sendMessage,
} from "@/lib/api/chat";
import { useAuth } from "@/hooks/useAuth";
import { useSessionStream } from "@/hooks/useSessionStream";
import type { Message, Session } from "@/types/chat";

interface UseWorkspaceResult {
  user: ReturnType<typeof useAuth>["user"];
  logout: ReturnType<typeof useAuth>["logout"];
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

  const [sessionId, setSessionId] = useState<string | undefined>(); // 当前工作区绑定的会话 id
  const [messages, setMessages] = useState<Message[]>([]); // 当前会话的消息列表
  const [sessions, setSessions] = useState<Session[]>([]); // 左侧会话列表
  const [homeDraft, setHomeDraft] = useState(""); // 首页输入框草稿内容
  const [isSending, setIsSending] = useState(false); // 是否正在发送消息或加载会话
  const [isLoadingSessions, setIsLoadingSessions] = useState(false); // 会话列表是否处于加载中
  const [error, setError] = useState<string | null>(null); // 全局错误提示

  const isHomeView = !sessionId && messages.length === 0; // 判断是否显示首页视图

  const ensureIsoTimestamp = (input?: string): string => {
    if (!input) return new Date().toISOString();
    const normalized = input.trim();
    if (/([zZ]|[+-]\d{2}:\d{2})$/.test(normalized)) {
      return normalized;
    }
    return `${normalized}Z`;
  };

  const normalizeMessage = (message: Message): Message => ({
    ...message,
    timestamp: ensureIsoTimestamp(message.timestamp),
  });

  // 加载当前用户的全部会话，并在无 token 时清空本地缓存
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
      const message = err instanceof Error ? err.message : "加载会话失败";
      setError(message);
      if (
        message.toLowerCase().includes("token") ||
        message.includes("未授权")
      ) {
        logout();
        router.push("/login");
      }
    } finally {
      setIsLoadingSessions(false);
    }
  }, [token, logout, router]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 将新消息合并进本地消息列表（基于 id upsert，确保去重）
  const mergeMessages = useCallback((incoming: Message | Message[]) => {
    const items = Array.isArray(incoming) ? incoming : [incoming];
    const normalizedItems = items.map(normalizeMessage);
    setMessages((prev) => {
      const next = [...prev];
      for (const item of normalizedItems) {
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

  const { streamingMessages, resetStreamingMessages, fileVersion } =
    useSessionStream({
      sessionId,
      mergeMessages,
      setError,
      setIsSending,
    });

  // 发送用户输入：必要时创建新会话，添加乐观消息，再落地真实响应
  const handleSend = useCallback(
    async (content: string) => {
      // 拦截跳转登录页
      if (!user || !token) {
        router.push("/login");
        return;
      }
      setIsSending(true);
      setError(null);
      // 用户消息乐观插入
      let optimisticId: string | null = null;
      try {
        let activeSessionId = sessionId;
        if (!activeSessionId) {
          // 没有会话时先向后端创建一个新的 session
          const session = await createSession(token);
          activeSessionId = session.id;
          setSessionId(session.id);
        }

        console.log("What is sessionid??", sessionId);
        optimisticId = `pending-${Date.now()}`;
        const optimisticMessage: Message = {
          id: optimisticId,
          session_id: activeSessionId,
          sender: "user",
          content,
          timestamp: new Date().toISOString(),
          agent: null,
        };
        mergeMessages(optimisticMessage);
        // 向后端提交真实请求，并用真实回合替换掉乐观消息
        const turn = await sendMessage(token, activeSessionId, content);
        // setMessages((prev) => {
        //   const next = prev.filter((message) => message.id !== optimisticId);
        //   const upsert = (item: Message) => {
        //     const index = next.findIndex((message) => message.id === item.id);
        //     if (index >= 0) {
        //       next[index] = item;
        //     } else {
        //       next.push(item);
        //     }
        //   };
        //   upsert(turn.user);
        //   turn.responses.forEach(upsert);
        //   return next;
        // });
        await loadSessions();
      } catch (err) {
        if (optimisticId) {
          setMessages((prev) =>
            prev.filter((message) => message.id !== optimisticId)
          );
        }
        setError(err instanceof Error ? err.message : "发送失败，请稍后再试");
      } finally {
        setIsSending(false);
      }
    },
    [user, token, router, sessionId, mergeMessages, loadSessions]
  );

  // 首页输入框提交后复用 handleSend
  const handleHomeSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const content = homeDraft.trim();
      if (!content) return;
      setHomeDraft("");
      await handleSend(content);
    },
    [homeDraft, handleSend]
  );

  // 用户点开某个历史会话时拉取整段历史消息
  const handleOpenSession = useCallback(
    async (id: string) => {
      if (!token) {
        router.push("/login");
        return;
      }
      setError(null);
      setIsSending(true);
      try {
        const history = await fetchMessages(token, id);
        setSessionId(id);
        setMessages(history);
        resetStreamingMessages();
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载会话失败");
      } finally {
        setIsSending(false);
      }
    },
    [token, router, resetStreamingMessages]
  );

  // 删除指定会话，必要时清空当前工作区
  const handleDeleteSession = useCallback(
    async (id: string) => {
      if (!token) {
        router.push("/login");
        return;
      }
      if (typeof window !== "undefined") {
        const confirmed = window.confirm("确定删除该会话吗？此操作不可恢复。");
        if (!confirmed) return;
      }
      setError(null);
      try {
        await deleteSession(token, id);
        if (sessionId === id) {
          setSessionId(undefined);
          setMessages([]);
          resetStreamingMessages();
        }
        await loadSessions();
      } catch (err) {
        setError(err instanceof Error ? err.message : "删除会话失败");
      }
    },
    [token, router, sessionId, loadSessions, resetStreamingMessages]
  );

  // 回到首页：清除选中的会话与临时流式数据
  const handleBackHome = useCallback(() => {
    setSessionId(undefined);
    setMessages([]);
    resetStreamingMessages();
    loadSessions();
  }, [loadSessions, resetStreamingMessages]);

  return {
    user,
    logout,
    sessionId,
    sessions,
    messages,
    streamingMessages,
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
    handleBackHome,
  };
}
