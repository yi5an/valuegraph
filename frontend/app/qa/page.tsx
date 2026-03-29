"use client";

import { useState, useRef, useEffect } from "react";
import { MessageCircle, Send, Bot, User, AlertCircle, ExternalLink } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp: Date;
}

interface QAResponse {
  success: boolean;
  data?: {
    answer: string;
    sources?: string[];
  };
  error?: string;
}

/**
 * Intelligent Q&A page with conversational interface.
 */
export default function QAPage(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/qa/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.content })
      });

      const data: QAResponse = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "问答请求失败");
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.data?.answer || "抱歉，我无法回答这个问题。",
        sources: data.data?.sources,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error("QA error:", err);
      setError(err instanceof Error ? err.message : "问答请求失败");
      
      // 添加错误消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "抱歉，处理您的问题时出现错误。请稍后重试。",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-primary">AI Assistant</p>
        <h1 className="mt-3 max-w-2xl text-3xl font-semibold text-white tablet:text-5xl">
          智能问答
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 tablet:text-base">
          基于金融知识图谱和实时数据，为您提供专业的投资分析问答服务
        </p>
      </section>

      <div className="flex-1 rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <MessageCircle className="h-16 w-16 text-slate-600 mb-4" />
              <p className="text-slate-400 text-sm">开始提问吧，我将为您提供专业的金融分析</p>
              <p className="text-slate-500 text-xs mt-2">例如："贵州茅台的投资价值如何？"或"推荐一些高ROE的股票"</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.role === "assistant" && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  
                  <div className={`max-w-[70%] ${message.role === "user" ? "order-first" : ""}`}>
                    <div
                      className={`rounded-2xl px-4 py-3 ${
                        message.role === "user"
                          ? "bg-primary text-white"
                          : "bg-white/5 text-slate-200 border border-white/10"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      
                      {/* 数据来源标签 */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <p className="text-xs text-slate-400 mb-2">数据来源：</p>
                          <div className="flex flex-wrap gap-2">
                            {message.sources.map((source, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1 rounded-full bg-slate-700/50 px-2 py-1 text-xs text-slate-300"
                              >
                                <ExternalLink className="h-3 w-3" />
                                {source}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 px-2">
                      {formatTime(message.timestamp)}
                    </p>
                  </div>

                  {message.role === "user" && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                      <User className="h-4 w-4 text-accent" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-4 rounded-xl border border-negative/30 bg-negative/10 p-3 flex items-center gap-2 text-sm text-negative">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入您的问题..."
            disabled={loading}
            className="flex-1 rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-primary px-6 py-3 text-sm font-medium text-white transition hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                思考中
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                发送
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
