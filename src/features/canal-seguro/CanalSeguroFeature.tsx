import React, { useState } from 'react';
import { CanalHeader } from './components/CanalHeader';
import { ContactDirectory } from './components/ContactDirectory';
import { ConversationFeed } from './components/ConversationFeed';
import { ClearanceCredentials } from './components/ClearanceCredentials';
import { AVILA_MOUNTAIN_PATH } from '../../constants/theme';
import { 
  CONTACT_PROFILES, 
  INITIAL_CHAT_MESSAGES, 
  AUDITOR_USER_PROFILE 
} from '../../constants/mockData';
import { ChatMessage } from '../../types';

interface CanalSeguroFeatureProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onNavigateHome?: () => void;
  onNotify?: (msg: string) => void;
}

export const CanalSeguroFeature: React.FC<CanalSeguroFeatureProps> = ({
  darkMode,
  onToggleDarkMode,
  onNavigateHome,
  onNotify,
}) => {
  const [selectedContactId, setSelectedContactId] = useState('c1');
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_CHAT_MESSAGES);
  const [mobileActivePane, setMobileActivePane] = useState<'contacts' | 'chat' | 'profile'>('chat');

  const handleSendMessage = (text: string) => {
    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      senderName: 'Carlos Méndez',
      senderInitials: 'CM',
      isSystem: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: text,
      sentReceiptLabel: 'Enviado',
    };
    setMessages((prev) => [...prev, newMsg]);
    onNotify?.('Mensaje transmitido mediante túnel E2EE con sello Ed25519.');
  };

  const handleSelectContact = (id: string) => {
    setSelectedContactId(id);
    setMobileActivePane('chat');
    const contact = CONTACT_PROFILES.find(c => c.id === id);
    if (contact && onNotify) {
      onNotify(`Conectado al canal seguro de ${contact.name}`);
    }
  };

  return (
    <div className="relative min-h-[720px] transition-colors">
      
      {/* Avila Mountain Subtle Silhouette Vector in Background */}
      <div className="absolute inset-x-0 top-6 pointer-events-none opacity-20 dark:opacity-10 flex items-start justify-center overflow-hidden z-0">
        <svg 
          className="w-full h-44 min-w-[900px] text-slate-400 dark:text-slate-600" 
          fill="currentColor" 
          viewBox="0 0 1200 240"
        >
          <path d={AVILA_MOUNTAIN_PATH} />
        </svg>
      </div>

      {/* Content wrapper */}
      <div className="relative z-10 space-y-4">
        
        {/* Top Header Bar with Title and Theme Switch */}
        <CanalHeader
          darkMode={darkMode}
          onToggleDarkMode={onToggleDarkMode}
          onNavigateHome={onNavigateHome}
        />

        {/* Mobile Navigation Tabs */}
        <div className="flex lg:hidden items-center justify-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl max-w-sm mx-auto text-xs font-semibold">
          <button
            onClick={() => setMobileActivePane('contacts')}
            className={`flex-1 py-1.5 rounded-lg transition-all ${
              mobileActivePane === 'contacts'
                ? 'bg-white dark:bg-slate-700 shadow-xs text-slate-900 dark:text-white font-bold'
                : 'text-slate-500'
            }`}
          >
            Contactos
          </button>
          <button
            onClick={() => setMobileActivePane('chat')}
            className={`flex-1 py-1.5 rounded-lg transition-all ${
              mobileActivePane === 'chat'
                ? 'bg-white dark:bg-slate-700 shadow-xs text-slate-900 dark:text-white font-bold'
                : 'text-slate-500'
            }`}
          >
            Conversación
          </button>
          <button
            onClick={() => setMobileActivePane('profile')}
            className={`flex-1 py-1.5 rounded-lg transition-all ${
              mobileActivePane === 'profile'
                ? 'bg-white dark:bg-slate-700 shadow-xs text-slate-900 dark:text-white font-bold'
                : 'text-slate-500'
            }`}
          >
            Credenciales
          </button>
        </div>

        {/* Main 3-Column Layout: Directory (3 cols) + Conversation Feed (6 cols) + Credentials (3 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6 items-start">
          
          {/* Column 1: Contacts Directory (3 cols) */}
          <div className={`lg:col-span-3 ${mobileActivePane === 'contacts' ? 'block' : 'hidden lg:block'}`}>
            <ContactDirectory
              contacts={CONTACT_PROFILES}
              selectedContactId={selectedContactId}
              onSelectContact={handleSelectContact}
            />
          </div>

          {/* Column 2: Conversation Feed (6 cols) */}
          <div className={`lg:col-span-6 ${mobileActivePane === 'chat' ? 'block' : 'hidden lg:block'}`}>
            <ConversationFeed
              messages={messages}
              onSendMessage={handleSendMessage}
            />
          </div>

          {/* Column 3: Profile & Credentials (3 cols) */}
          <div className={`lg:col-span-3 ${mobileActivePane === 'profile' ? 'block' : 'hidden lg:block'}`}>
            <ClearanceCredentials
              profile={AUDITOR_USER_PROFILE}
            />
          </div>

        </div>

      </div>

    </div>
  );
};
