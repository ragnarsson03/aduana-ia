import React, { useState } from 'react';
import { Paperclip, Send, FileText, Settings, ShieldCheck } from 'lucide-react';
import { ChatMessage } from '../../../types';

interface ChatThreadProps {
  messages: ChatMessage[];
  onSendMessage?: (text: string) => void;
}

export const ChatThread: React.FC<ChatThreadProps> = ({
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
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs flex flex-col h-[650px] justify-between transition-colors">
      
      {/* Conversation Header */}
      <div className="pb-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-300 font-bold text-xs flex items-center justify-center">
            CM
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 dark:text-white">
              Carlos Méndez — Auditor Principal
            </h4>
            <p className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Sesión Confidencial | Cifrado E2E Activo
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 text-xs rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">
          CM A: avatar
        </span>
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 text-xs">
        {messages.map((msg) => {
          return (
            <div key={msg.id} className="flex items-start space-x-2.5">
              {msg.isSystem ? (
                <div className="w-7 h-7 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-[#4f46e5] border border-indigo-200 dark:border-indigo-800/50 flex items-center justify-center text-xs shrink-0 mt-0.5">
                  <Settings className="w-3.5 h-3.5" />
                </div>
              ) : (
                <div className="w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  {msg.senderInitials || 'DR'}
                </div>
              )}

              <div className="flex-1">
                <div className="flex items-baseline justify-between mb-1">
                  <span className="font-bold text-slate-900 dark:text-white">
                    {msg.senderName}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {msg.timestamp}
                  </span>
                </div>

                <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-tl-none text-slate-700 dark:text-slate-200 leading-relaxed">
                  {msg.content}
                </div>

                {/* Attached Encrypted Document Box */}
                {msg.attachment && (
                  <div className="mt-2 p-3 bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 rounded-xl flex items-center space-x-3">
                    <span className="text-xl">📄</span>
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-rose-800 dark:text-rose-300 truncate font-mono text-[11px]">
                        {msg.attachment.title}
                      </p>
                      <p className="text-[10px] text-rose-600 dark:text-rose-400">
                        {msg.attachment.description}
                      </p>
                    </div>
                  </div>
                )}

                {/* Masked PII Example pill */}
                {msg.maskedToken && (
                  <div className="mt-2">
                    <span className="inline-block font-mono bg-amber-200/60 dark:bg-amber-950/70 text-amber-900 dark:text-amber-300 px-2 py-0.5 rounded text-[11px] font-bold">
                      {msg.maskedToken}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Chat Input Bar */}
      <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
        <div className="relative flex items-center">
          <input 
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Escribe un mensaje cifrado..." 
            className="w-full pl-4 pr-20 py-2.5 text-xs rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-hidden focus:ring-1 focus:ring-[#4f46e5] text-slate-800 dark:text-slate-200"
          />
          <div className="absolute right-2 flex items-center space-x-1.5">
            <button 
              type="button"
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              title="Adjuntar archivo confidencial"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button 
              type="button"
              onClick={handleSend}
              className="w-7 h-7 rounded-full bg-[#4f46e5] text-white flex items-center justify-center text-xs hover:bg-indigo-600 shadow-2xs transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        
        <div className="text-[10px] text-slate-400 text-right mt-1 font-mono">
          Enviado con hash Ed25519
        </div>
      </div>

    </div>
  );
};
