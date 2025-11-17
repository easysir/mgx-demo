"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  API_BASE,
  createSession,
  deleteSession,
  fetchMessages,
  listSessions,
  sendMessage,
} from "@/lib/api/chat";
import { useAuth } from "@/hooks/useAuth";
import type { Message, SenderRole, Session, StreamEvent } from "@/types/chat";

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
  const [streamingMessages, setStreamingMessages] = useState<
    Record<string, Message>
  >({}); // 尚未完成的流式消息缓存
  const [fileVersion, setFileVersion] = useState(0); // 文件/上下文版本号，用于触发刷新

  const isHomeView = !sessionId && messages.length === 0; // 判断是否显示首页视图

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

  // 发送用户输入：必要时创建新会话，添加乐观消息，再落地真实响应
  const handleSend = useCallback(
    async (content: string) => {
      if (!user || !token) {
        router.push("/login");
        return;
      }
      setIsSending(true);
      setError(null);
      let optimisticId: string | null = null;
      try {
        let activeSessionId = sessionId;
        if (!activeSessionId) {
          // 没有会话时先向后端创建一个新的 session
          const session = await createSession(token);
          activeSessionId = session.id;
          setSessionId(session.id);
        }
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
        setStreamingMessages({});
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载会话失败");
      } finally {
        setIsSending(false);
      }
    },
    [token, router]
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
          setStreamingMessages({});
        }
        await loadSessions();
      } catch (err) {
        setError(err instanceof Error ? err.message : "删除会话失败");
      }
    },
    [token, router, sessionId, loadSessions]
  );

  // 回到首页：清除选中的会话与临时流式数据
  const handleBackHome = useCallback(() => {
    setSessionId(undefined);
    setMessages([]);
    setStreamingMessages({});
    loadSessions();
  }, [loadSessions]);

  // 建立 WebSocket 监听当前会话的流式事件（工具调用、状态、消息等）
  useEffect(() => {
    if (!sessionId) {
      setStreamingMessages({});
      return;
    }
    const activeSessionId = sessionId;
    let socket: WebSocket | null = null;
    let cancelled = false;

    // 允许通过环境变量或 API_BASE 推导出 WS 地址
    const resolveWsBase = () => {
      const configured = process.env.NEXT_PUBLIC_WS_BASE_URL;
      if (configured) return configured.replace(/\/$/, "");
      try {
        const apiUrl = new URL(API_BASE);
        const protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
        return `${protocol}//${apiUrl.host}`;
      } catch {
        if (typeof window !== "undefined") {
          return window.location.origin.replace(/^http/, "ws");
        }
        return "ws://127.0.0.1:8000";
      }
    };

    const wsBase = resolveWsBase();
    const url = `${wsBase}/api/ws/sessions/${activeSessionId}`;
    try {
      socket = new WebSocket(url);
    } catch (err) {
      console.error("WebSocket connection failed", err);
      return;
    }

    // 处理服务端推送的各种流式事件
    socket.onmessage = (event) => {
      if (cancelled) return;
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        const effectiveSession = data.session_id ?? activeSessionId;
        if (!effectiveSession || effectiveSession !== activeSessionId) return;

        // 刷新文件列表
        if (data.type === "file_change") {
          setFileVersion((prev) => prev + 1);
          return;
        }

        const messageId = data.message_id ?? "";
        if (!messageId) return;
        const stableMessageId: string = messageId;

        if (data.type === "tool_call") {
          // 工具调用：直接落地为一条普通消息
          const eventTimestamp = data.timestamp
            ? new Date(data.timestamp).toISOString()
            : new Date().toISOString();
          const content = data.content ?? `[工具调用] ${data.tool ?? ""}`;
          mergeMessages({
            id: messageId,
            session_id: activeSessionId,
            sender: data.sender ?? "agent",
            agent: data.agent ?? null,
            content,
            timestamp: eventTimestamp,
          });
          return;
        }

        if (data.type === "message" && data.sender === "user") {
          return;
        }

        if (data.type === "error") {
          // 错误事件需要在界面上展示并终止流式状态
          const errorContent = data.content || "LLM 调用失败，请稍后重试";
          setError(errorContent);
          setIsSending(false);
          setStreamingMessages({});
          mergeMessages({
            id: messageId,
            session_id: activeSessionId,
            sender: "status",
            agent: data.agent ?? "Mike",
            content: errorContent,
            timestamp: new Date().toISOString(),
          });
          return;
        }

        // 将流式 token 累积到临时消息，final 后写回正式列表
        setStreamingMessages((prev) => {
          const previousEntry = prev[stableMessageId] as Message | undefined;
          const inferredSender: SenderRole = data.sender ?? "agent";
          const inferredTimestamp =
            previousEntry?.timestamp ??
            data.timestamp ??
            new Date().toISOString();
          const baseMessage: Message = previousEntry ?? {
            id: stableMessageId,
            session_id: activeSessionId,
            sender: inferredSender,
            agent: data.agent ?? null,
            content: "",
            timestamp: inferredTimestamp,
          };

          const updated: Message =
            data.type === "status"
              ? {
                  ...baseMessage,
                  sender: "status",
                  agent: data.agent ?? "Mike",
                  content: data.content ?? "",
                }
              : {
                  ...baseMessage,
                  content: baseMessage.content + (data.content ?? ""),
                };

          if (data.final) {
            mergeMessages({
              ...updated,
              timestamp: baseMessage.timestamp,
            });
            const nextState = { ...prev };
            delete nextState[stableMessageId];
            return nextState;
          }
          return { ...prev, [stableMessageId]: updated };
        });
      } catch (err) {
        console.error("Failed to parse stream event", err);
      }
    };

    socket.onerror = (event) => {
      console.error("WebSocket error", event);
    };

    return () => {
      cancelled = true;
      setStreamingMessages({});
      socket?.close();
    };
  }, [sessionId, mergeMessages]);

  const streamingMessagesList = useMemo(
    () => Object.values(streamingMessages),
    [streamingMessages]
  );

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
    handleBackHome,
  };
}
