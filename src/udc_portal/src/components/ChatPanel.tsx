import { useEffect, useRef, useState } from "react";
import { useStreamingChat } from "@/hooks/useStreamingChat";
import type { StreamMessage } from "@/hooks/useStreamingChat";

interface ChatPanelProps {
  endpoint: string;
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function LoadingDots(): React.JSX.Element {
  return (
    <div className="flex gap-1 px-3 py-2">
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
    </div>
  );
}

function MessageBubble({ msg }: { msg: StreamMessage }): React.JSX.Element {
  const [showTime, setShowTime] = useState(false);
  const isUser = msg.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      <div className="relative max-w-[75%]">
        <div
          className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {msg.content || <LoadingDots />}
        </div>
        {showTime && (
          <span
            className={`absolute -bottom-5 text-[10px] text-gray-400 ${
              isUser ? "right-1" : "left-1"
            }`}
          >
            {formatTime(msg.timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}

export default function ChatPanel({ endpoint }: ChatPanelProps): React.JSX.Element {
  const { messages, sendMessage, isStreaming, connectionState } = useStreamingChat(endpoint);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const handleSend = (): void => {
    if (!input.trim() || isStreaming) return;
    void sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col rounded-lg border border-gray-200 bg-white">
      {/* Connection status */}
      {connectionState === "connecting" && (
        <div className="border-b border-blue-100 bg-blue-50 px-3 py-1.5 text-center text-xs text-blue-600">
          Connecting…
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-400">
              Start the conversation. Ask anything about your data.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {isStreaming && messages.at(-1)?.role !== "assistant" && (
          <div className="flex justify-start">
            <LoadingDots />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-3">
        <div className="flex gap-2">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message… (Shift+Enter for newline)"
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
