"use client";

import { Dispatch, SetStateAction, useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE } from "@/lib/api/chat";
import type { Message, SenderRole, StreamEvent } from "@/types/chat";

interface UseSessionStreamArgs {
  sessionId?: string;
  mergeMessages: (incoming: Message | Message[]) => void;
  setError: Dispatch<SetStateAction<string | null>>;
  setIsSending: Dispatch<SetStateAction<boolean>>;
}

interface UseSessionStreamResult {
  streamingMessages: Message[];
  resetStreamingMessages: () => void;
  fileVersion: number;
}

export function useSessionStream({
  sessionId,
  mergeMessages,
  setError,
  setIsSending,
}: UseSessionStreamArgs): UseSessionStreamResult {
  const [streamingMessages, setStreamingMessages] = useState<Record<string, Message>>({});
  const [fileVersion, setFileVersion] = useState(0);

  const resetStreamingMessages = useCallback(() => {
    setStreamingMessages({});
  }, []);

  useEffect(() => {
    if (!sessionId) {
      resetStreamingMessages();
      return;
    }
    const activeSessionId = sessionId;
    let socket: WebSocket | null = null;
    let cancelled = false;

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

    socket.onmessage = (event) => {
      if (cancelled) return;
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        const effectiveSession = data.session_id ?? activeSessionId;
        if (!effectiveSession || effectiveSession !== activeSessionId) return;

        if (data.type === "file_change") {
          setFileVersion((prev) => prev + 1);
          return;
        }

        const messageId = data.message_id ?? "";
        if (!messageId) return;
        const stableMessageId = messageId;

        if (data.type === "tool_call") {
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
          const errorContent = data.content || "LLM 调用失败，请稍后重试";
          setError(errorContent);
          setIsSending(false);
          resetStreamingMessages();
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

        setStreamingMessages((prev) => {
          const previousEntry = prev[stableMessageId] as Message | undefined;
          const inferredSender: SenderRole = data.sender ?? "agent";
          const inferredTimestamp =
            previousEntry?.timestamp ?? data.timestamp ?? new Date().toISOString();
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
      resetStreamingMessages();
      socket?.close();
    };
  }, [sessionId, mergeMessages, setError, setIsSending, resetStreamingMessages]);

  const streamingMessagesList = useMemo(
    () => Object.values(streamingMessages),
    [streamingMessages]
  );

  return {
    streamingMessages: streamingMessagesList,
    resetStreamingMessages,
    fileVersion,
  };
}

