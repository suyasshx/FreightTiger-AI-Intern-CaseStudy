import React, { useState, useRef, useEffect } from 'react';
import {
  Brain, Send, Sparkles, ShieldCheck,
  Bot, User, FileText
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { QAResponse } from '../types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  evidenceNotes?: string[];
  metricsCited?: Record<string, any>;
  timestamp: string;
}

export const AIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm1',
      sender: 'assistant',
      text: (
        "Hello! I am your RouteGuard Intelligence Assistant. " +
        "I can answer questions regarding freight transportation costs, anomalous route-weeks, " +
        "historical baseline shifts, and contextual evidence gate decisions.\n\n" +
        "All my responses are grounded strictly in the computed pipeline results and verified context notes — zero hallucinated claims."
      ),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    "Why did Chennai-Bangalore become more expensive in March 2025?",
    "Which routes have unexplained cost increases requiring review?",
    "How many anomalies have valid supporting notes?",
    "Why was contextual note N005 rejected?",
    "Why did the system reject note N006 for Mumbai-Pune?",
    "Compare Ahmedabad-Mumbai with its historical past average."
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res: QAResponse = await apiClient.sendChatMessage(textToSend);

      const botMsg: Message = {
        id: `b-${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        evidenceNotes: res.evidence_notes,
        metricsCited: res.metrics_cited,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `Error connecting to intelligence assistant: ${err.message || 'Unknown error'}. Please check backend connection.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Assistant Title & Status */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-400 p-0.5">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Brain className="w-5 h-5 text-sky-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white tracking-tight">AI Cost Intelligence Assistant</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Grounded in Verified Data
              </span>
            </div>
            <p className="text-xs text-slate-400">Ask natural-language questions about route rates, anomalies, and note validations.</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Deterministic Tool Calling</span>
        </div>
      </div>

      {/* Suggested Prompts Carousel */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
        <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 ml-1" />
        <span className="text-[11px] font-semibold text-slate-400 flex-shrink-0">Suggested:</span>
        {suggestedPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="flex-shrink-0 px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-xs border border-slate-800 transition shadow-sm"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 backdrop-blur-md h-[480px] flex flex-col overflow-hidden shadow-2xl">
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex space-x-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/25 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-sky-400" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                  m.sender === 'user'
                    ? 'bg-sky-600 text-white rounded-tr-none'
                    : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-none shadow-md'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* Evidence Note Citations */}
                {m.evidenceNotes && m.evidenceNotes.length > 0 && (
                  <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-semibold flex items-center">
                      <FileText className="w-3 h-3 mr-1 text-indigo-400" />
                      Cited Notes:
                    </span>
                    {m.evidenceNotes.map((nid) => (
                      <span
                        key={nid}
                        className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      >
                        {nid}
                      </span>
                    ))}
                  </div>
                )}

                <div className={`text-[10px] text-right ${m.sender === 'user' ? 'text-sky-200' : 'text-slate-500'}`}>
                  {m.timestamp}
                </div>
              </div>
              {m.sender === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-slate-300" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex space-x-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/25 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-sky-400" />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs text-slate-400 flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]" />
                <span className="ml-2 font-mono text-[11px] text-slate-400">Querying verified pipeline database...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input Bar */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              placeholder="Ask about route rates, anomalies, or note validation decisions..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-xs font-semibold flex items-center space-x-1.5 transition shadow-lg shadow-sky-600/20"
            >
              <span>Ask</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
