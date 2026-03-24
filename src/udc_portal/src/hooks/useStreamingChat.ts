import { useState, useCallback, useRef } from "react";

export interface StreamMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

type ConnectionState = "disconnected" | "connecting" | "connected";

export function useStreamingChat(endpoint: string) {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const abortRef = useRef<AbortController | null>(null);
  const streamingMsgIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      const userMsg: StreamMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);

      const assistantId = crypto.randomUUID();
      streamingMsgIdRef.current = assistantId;
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", timestamp: Date.now() },
      ]);
      setIsStreaming(true);
      setConnectionState("connecting");

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content.trim(), session_id: sessionId }),
          signal: controller.signal,
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (!response.body) throw new Error("No response body");

        setConnectionState("connected");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;
            const payload = line.slice(5).trim();
            if (payload === "[DONE]") break;

            try {
              const parsed = JSON.parse(payload) as { content?: string; session_id?: string };
              if (parsed.session_id) setSessionId(parsed.session_id);
              if (parsed.content) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: m.content + parsed.content } : m,
                  ),
                );
              }
            } catch {
              // Treat non-JSON data lines as plain text chunks
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + payload } : m,
                ),
              );
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId && !m.content
                ? { ...m, content: "Sorry, an error occurred. Please try again." }
                : m,
            ),
          );
        }
      } finally {
        setIsStreaming(false);
        setConnectionState("disconnected");
        streamingMsgIdRef.current = null;
      }
    },
    [endpoint, sessionId],
  );

  const newSession = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setSessionId(crypto.randomUUID());
    setConnectionState("disconnected");
    setIsStreaming(false);
  }, []);

  return {
    messages,
    sendMessage,
    connectionState,
    isConnected: connectionState === "connected",
    isStreaming,
    sessionId,
    newSession,
  };
}
