import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { ContactList } from './components/ContactList';
import { ChatThread } from './components/ChatThread';
import { UserProfileCard } from './components/UserProfileCard';
import { 
  CONTACT_PROFILES, 
  INITIAL_CHAT_MESSAGES, 
  AUDITOR_USER_PROFILE 
} from '../../constants/mockData';
import { ChatMessage } from '../../types';

interface CanalSeguroFeatureProps {
  onBackToPasarela: () => void;
  onNotify?: (msg: string) => void;
}

export const CanalSeguroFeature: React.FC<CanalSeguroFeatureProps> = ({
  onBackToPasarela,
  onNotify,
}) => {
  const [selectedContactId, setSelectedContactId] = useState('c1');
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_CHAT_MESSAGES);

  const handleSendMessage = (text: string) => {
    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      senderName: 'Carlos Méndez',
      senderInitials: 'CM',
      isSystem: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: text,
    };
    setMessages((prev) => [...prev, newMsg]);
    onNotify?.('Mensaje transmitido mediante túnel E2EE con sello Ed25519.');
  };

  return (
    <div className="space-y-6">
      {/* Top Banner for Secure Channel */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs transition-colors">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Aduana IA — Canal Seguro Cifrado Punto a Punto (E2EE)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Canal de auditoría confidencial con desidentificación dinámica y verificación biométrica
            </p>
          </div>
        </div>

        <button
          onClick={onBackToPasarela}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors inline-flex items-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Volver a Pasarela</span>
        </button>
      </div>

      {/* Main 3-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Column Left: Contacts (3 cols) */}
        <div className="lg:col-span-3">
          <ContactList
            contacts={CONTACT_PROFILES}
            selectedContactId={selectedContactId}
            onSelectContact={(id) => setSelectedContactId(id)}
          />
        </div>

        {/* Column Center: Active Conversation Thread (6 cols) */}
        <div className="lg:col-span-6">
          <ChatThread
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>

        {/* Column Right: User Profile & Security Clearance (3 cols) */}
        <div className="lg:col-span-3">
          <UserProfileCard
            profile={AUDITOR_USER_PROFILE}
          />
        </div>
      </div>
    </div>
  );
};
