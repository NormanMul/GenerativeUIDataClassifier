import { useState, useEffect, useRef } from "react";
import { useStreamingChat } from "@/hooks/useStreamingChat";
import type { StreamMessage } from "@/hooks/useStreamingChat";

const CHAT_ENDPOINT = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api/chat`;

function LoadingDots(): React.JSX.Element {
  return (
    <span className="inline-flex gap-1">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
    </span>
  );
}

function ToolCallIndicator(): React.JSX.Element {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
      <div className="h-3 w-3 animate-spin rounded-full border-2 border-amber-300 border-t-amber-600" />
      Executing tools…
    </div>
  );
}

function MessageBubble({ msg }: { msg: StreamMessage }): React.JSX.Element {
  const [showTime, setShowTime] = useState(false);
  const isUser = msg.role === "user";

  // Simple text rendering (sanitized – no raw HTML)
  const renderContent = (text: string) => {
    if (!text) return <LoadingDots />;
    // Basic markdown-like rendering: **bold**, `code`, newlines
    return text.split("\n").map((line, i) => (
      <span key={i}>
        {i > 0 && <br />}
        {line.split(/(`[^`]+`)/).map((part, j) =>
          part.startsWith("`") && part.endsWith("`") ? (
            <code
              key={j}
              className={`rounded px-1 py-0.5 font-mono text-xs ${
                isUser ? "bg-blue-500/30" : "bg-gray-200"
              }`}
            >
              {part.slice(1, -1)}
            </code>
          ) : (
            <span key={j}>{part}</span>
          ),
        )}
      </span>
    ));
  };

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      <div className="relative max-w-[75%]">
        {/* Avatar */}
        {!isUser && (
          <span className="mb-1 block text-xs font-medium text-gray-500">UDC Assistant</span>
        )}
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "rounded-br-md bg-blue-600 text-white"
              : "rounded-bl-md bg-gray-100 text-gray-800"
          }`}
        >
          {renderContent(msg.content)}
        </div>
        {showTime && (
          <span
            className={`absolute -bottom-5 text-[10px] text-gray-400 ${
              isUser ? "right-1" : "left-1"
            }`}
          >
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>
    </div>
  );
}

export default function ChatInterface(): React.JSX.Element {
  const {
    messages,
    sendMessage,
    isStreaming,
    connectionState,
    sessionId,
    newSession,
  } = useStreamingChat(CHAT_ENDPOINT);

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    void sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
        <div className="flex items-center gap-3">
          {/* Connection indicator */}
          <span className="flex items-center gap-1.5 text-xs text-gray-400">
            <span
              className={`h-2 w-2 rounded-full ${
                connectionState === "connected"
                  ? "bg-green-500"
                  : connectionState === "connecting"
                    ? "animate-pulse bg-yellow-500"
                    : "bg-gray-300"
              }`}
            />
            {connectionState === "connected" ? "Connected" : connectionState === "connecting" ? "Connecting" : "Ready"}
          </span>

          {/* Session ID */}
          <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-[10px] text-gray-400">
            {sessionId.slice(0, 8)}
          </span>

          {/* New chat */}
          <button
            onClick={newSession}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
          >
            + New Chat
          </button>
        </div>
      </div>

      {/* Message list */}
      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto rounded-lg border border-gray-200 bg-white p-4"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <span className="text-4xl">💬</span>
            <p className="mt-3 text-sm font-medium text-gray-500">
              Start a conversation with the UDC assistant
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Ask about your data, create dashboards, or explore pipelines.
            </p>
          </div>
        )}
        {messages.map((msg: StreamMessage) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {isStreaming && messages.at(-1)?.content === "" && <ToolCallIndicator />}
      </div>

      {/* Input area */}
      <div className="mt-3 flex gap-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your data… (Shift+Enter for newline)"
          className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isStreaming ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          ) : (
            "Send"
          )}
        </button>
      </div>
    </div>
  );
}
