import React, { useState } from 'react';
import { 
  Paperclip, 
  Send, 
  FileText, 
  Settings, 
  ShieldCheck 
} from 'lucide-react';
import { ChatMessage } from '../../../types';

interface ConversationFeedProps {
  messages: ChatMessage[];
  onSendMessage?: (text: string) => void;
}

export const ConversationFeed: React.FC<ConversationFeedProps> = ({
  messages,
  onSendMessage,
}) => {
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim()) return;
    onSendMessage?.(inputText);
    setInputText('');
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-xs flex flex-col h-[650px] justify-between transition-colors">
      
      {/* 1. Conversation Header */}
      <div className="pb-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        
        {/* Left: Avatar + Title + E2E Status */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <span className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-950/70 text-[#4f46e5] dark:text-indigo-300 font-bold text-xs flex items-center justify-center select-none shadow-2xs">
              CM
            </span>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" />
          </div>

          <div>
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white tracking-tight">
              Carlos Méndez — Auditor Principal
            </h4>
            <div className="flex items-center gap-1.5 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium font-mono mt-0.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Sesión Confidencial | Cifrado E2E</span>
            </div>
          </div>
        </div>

        {/* Right: Pill Badge */}
        <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-indigo-100 dark:bg-indigo-950 text-[#4f46e5] dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
          CM A: avatar
        </span>
      </div>

      {/* 2. Message History Feed */}
      <div className="flex-1 overflow-y-auto py-4 space-y-5 pr-1.5 text-xs">
        {messages.map((msg) => {
          return (
            <div key={msg.id} className="flex items-start space-x-3">
              
              {/* Sender Avatar */}
              {msg.isSystem ? (
                <div className="w-7 h-7 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/60 flex items-center justify-center text-xs shrink-0 mt-0.5 shadow-2xs">
                  <Settings className="w-3.5 h-3.5" />
                </div>
              ) : (
                <div className="w-7 h-7 rounded-full bg-[#ebd8c3] text-[#6d4c26] dark:bg-[#543b1e] dark:text-[#ebd8c3] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5 shadow-2xs select-none">
                  {msg.senderInitials || 'DR'}
                </div>
              )}

              {/* Message Content Body */}
              <div className="flex-1 max-w-2xl">
                
                {/* Sender Name & Timestamp */}
                <div className="flex items-baseline justify-between mb-1.5">
                  <span className="font-bold text-slate-900 dark:text-white text-xs">
                    {msg.senderName}
                  </span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                    {msg.timestamp}
                  </span>
                </div>

                {/* Primary Bubble */}
                <div className="p-3 bg-slate-100/90 dark:bg-slate-800/80 rounded-2xl rounded-tl-xs text-slate-700 dark:text-slate-200 leading-relaxed font-sans shadow-2xs">
                  {msg.content}
                </div>

                {/* Attached Classified Document Box */}
                {msg.attachment && (
                  <div className="mt-2.5 p-3 rounded-xl bg-white dark:bg-slate-800/90 border border-rose-200 dark:border-rose-900/60 flex items-start space-x-3 shadow-2xs">
                    <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 shrink-0">
                      <FileText className="w-5 h-5 stroke-[1.8]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-slate-800 dark:text-slate-200 text-xs font-mono">
                        {msg.attachment.title}
                      </p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        {msg.attachment.description}
                      </p>
                      {msg.attachment.code && (
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                          {msg.attachment.code}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* PII Masked Token Example Box */}
                {msg.maskedToken && (
                  <div className="mt-3 p-3 bg-slate-50/70 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800/70">
                    {msg.tokenExampleLabel && (
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-1.5 font-medium">
                        {msg.tokenExampleLabel}
                      </p>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="inline-block font-mono bg-[#ffddb8]/80 dark:bg-amber-950/80 text-[#653e00] dark:text-amber-300 border border-amber-300 dark:border-amber-800 px-2.5 py-0.5 rounded-lg text-xs font-bold tracking-wide">
                        {msg.maskedToken}
                      </span>
                      
                      <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400">
                        {msg.secondTimestamp && <span>{msg.secondTimestamp}</span>}
                        {msg.sentReceiptLabel && (
                          <span className="text-slate-500 dark:text-slate-400 font-medium">
                            {msg.sentReceiptLabel}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}

              </div>

            </div>
          );
        })}
      </div>

      {/* 3. Chat Input Bar matching screenshot */}
      <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Escribe un mensaje cifrado..."
            className="w-full pl-4 pr-24 py-3 text-xs rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 focus:outline-hidden focus:ring-1 focus:ring-[#4f46e5] text-slate-800 dark:text-slate-200 placeholder-slate-400 transition-all font-sans"
          />

          <div className="absolute right-2.5 flex items-center space-x-2">
            <button
              type="button"
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Adjuntar archivo clasificado"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={handleSend}
              className="w-8 h-8 rounded-xl bg-[#4f46e5] hover:bg-indigo-600 text-white flex items-center justify-center text-xs shadow-xs transition-colors"
              title="Transmitir con Ed25519"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};
