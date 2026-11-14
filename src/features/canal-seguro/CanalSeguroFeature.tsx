import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Send, 
  Paperclip, 
  Lock, 
  CheckCheck, 
  Info, 
  UserCheck, 
  KeyRound,
  Radio,
  FileText
} from 'lucide-react';
import { ContactProfile, InstitutionalChannel, ChatMessage } from '../../types/secure-channel';
import { AuthUser } from '../../types/auth';
import { 
  MOCK_CHANNELS, 
  MOCK_CONTACTS_WITH_CREDENTIALS, 
  INITIAL_CHAT_MESSAGES 
} from '../../constants/mockAuth';
import { ContactCredentialsModal } from './components/ContactCredentialsModal';

interface CanalSeguroFeatureProps {
  currentUser?: AuthUser;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onNavigateHome?: () => void;
  onNotify?: (msg: string) => void;
}

export const CanalSeguroFeature: React.FC<CanalSeguroFeatureProps> = ({
  currentUser,
  darkMode,
  onToggleDarkMode,
  onNavigateHome,
  onNotify,
}) => {
  const [activeChannelId, setActiveChannelId] = useState<string>('auditoria-general');
  const [selectedContact, setSelectedContact] = useState<ContactProfile>(MOCK_CONTACTS_WITH_CREDENTIALS[0]);
  const [inspectingContact, setInspectingContact] = useState<ContactProfile | null>(null);
  const [isCredentialsModalOpen, setIsCredentialsModalOpen] = useState(false);
  
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_CHAT_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileTab, setMobileTab] = useState<'sidebar' | 'chat'>('chat');

  // Filtered contacts based on search
  const filteredContacts = MOCK_CONTACTS_WITH_CREDENTIALS.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectContact = (contact: ContactProfile) => {
    setSelectedContact(contact);
    setMobileTab('chat');
    onNotify?.(`Canal seguro con ${contact.name} establecido con cifrado E2EE.`);
  };

  const handleInspectContact = (contact: ContactProfile, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setInspectingContact(contact);
    setIsCredentialsModalOpen(true);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Check if input contains PII pattern like cédula V-XXXXXXX
    const cedulaRegex = /([VvEeJjGg]-?\d{1,2}\.?\d{3}\.?\d{3})/g;
    const hasPII = cedulaRegex.test(inputText);
    const maskedContent = inputText.replace(cedulaRegex, '[CÉDULA OCULTA]');

    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      senderName: currentUser ? currentUser.shortName : 'Usted (Operador)',
      senderInitials: currentUser ? currentUser.avatarText : 'OP',
      senderRole: currentUser ? currentUser.roleLabel : 'Operador de Guardia',
      isCurrentUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' UTC',
      content: maskedContent,
      piiMasked: hasPII,
      piiType: hasPII ? 'CÉDULA OCULTA' : undefined,
      piiHash: hasPII ? '89ab...7df1' : undefined,
      verifiedDelivery: true,
    };

    setMessages(prev => [...prev, newMsg]);
    setInputText('');

    if (hasPII) {
      onNotify?.('Shield activó ofuscación homomórfica: Cédula sanitizada antes de emisión.');
    } else {
      onNotify?.('Mensaje transmitido y sellado con hash SHA-256 en memoria confinada.');
    }
  };

  const handleInsertSamplePII = () => {
    setInputText('Solicitud de trámite aduanero vinculada a la cédula V-18.452.931 para liquidación arancelaria.');
    onNotify?.('Texto de prueba con cédula insertado. Al enviar será ofuscado automáticamente.');
  };

  return (
    <div className="relative rounded-2xl bg-white dark:bg-[#090d16] border border-neutral-200/90 dark:border-neutral-800/90 shadow-xl overflow-hidden flex flex-col min-h-[760px] max-h-[880px] transition-colors select-none">
      
      {/* Top Global Context Strip (Canal Seguro v2.4) */}
      <div className="h-14 border-b border-neutral-200/80 dark:border-neutral-800/80 px-4 sm:px-6 flex items-center justify-between bg-white/95 dark:bg-[#090d16]/95 backdrop-blur-md shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-primary dark:text-indigo-400 flex items-center justify-center font-bold border border-indigo-200/50 dark:border-indigo-800/40">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-tight text-sm text-neutral-900 dark:text-white">
              Aduana IA
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300 font-medium border border-neutral-200/60 dark:border-neutral-700/60">
              Canal Seguro v2.4
            </span>
          </div>
        </div>

        {/* Center Live Badges */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 text-xs font-medium border border-emerald-200/50 dark:border-emerald-800/40 shadow-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>Cifrado Homomórfico & Shield PII Activo</span>
          </div>
          <span className="text-neutral-300 dark:text-neutral-700">|</span>
          <span className="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
            ID Sesión: sec-992a-fed
          </span>
        </div>

        {/* Right Info: Clearance Indicator */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleInspectContact(selectedContact)}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-colors"
            title="Ver credenciales del usuario activo"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Ver Credenciales de Contacto</span>
            <span className="sm:hidden">Credenciales</span>
          </button>
        </div>
      </div>

      {/* Mobile Tab Switcher */}
      <div className="flex md:hidden border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#0c121e] p-1">
        <button
          onClick={() => setMobileTab('sidebar')}
          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            mobileTab === 'sidebar'
              ? 'bg-white dark:bg-slate-700 text-neutral-900 dark:text-white shadow-xs'
              : 'text-neutral-500'
          }`}
        >
          Canales & Contactos
        </button>
        <button
          onClick={() => setMobileTab('chat')}
          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            mobileTab === 'chat'
              ? 'bg-white dark:bg-slate-700 text-neutral-900 dark:text-white shadow-xs'
              : 'text-neutral-500'
          }`}
        >
          Conversación ({selectedContact.name})
        </button>
      </div>

      {/* Main Two-Pane Body */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT SIDEBAR (28% width / responsive) */}
        <aside className={`w-full md:w-[30%] min-w-[280px] max-w-[360px] border-r border-neutral-200/80 dark:border-neutral-800/80 bg-neutral-50/60 dark:bg-[#0c121e]/80 flex flex-col shrink-0 ${
          mobileTab === 'sidebar' ? 'block' : 'hidden md:flex'
        }`}>
          {/* Search Box */}
          <div className="p-3 border-b border-neutral-200/60 dark:border-neutral-800/60">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 dark:text-neutral-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar usuario o canal..."
                className="w-full bg-white dark:bg-[#141b29] text-xs pl-8 pr-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-800 text-neutral-800 dark:text-neutral-200 placeholder-neutral-400 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          {/* Scrollable Channels and Users List */}
          <div className="flex-1 overflow-y-auto px-2 py-3 space-y-5">
            {/* Canales Institucionales */}
            <div>
              <div className="px-2 pb-1.5 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                <span>Canales Institucionales</span>
                <span className="text-[10px] font-mono font-normal">2 ACTIVOS</span>
              </div>
              <div className="space-y-0.5">
                {MOCK_CHANNELS.map(ch => {
                  const isActive = activeChannelId === ch.id;
                  return (
                    <button
                      key={ch.id}
                      onClick={() => {
                        setActiveChannelId(ch.id);
                        onNotify?.(`Sintonizado a ${ch.name}`);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-neutral-200/80 dark:bg-neutral-800/80 text-neutral-900 dark:text-white shadow-xs'
                          : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span className={`font-mono text-sm font-semibold ${isActive ? 'text-primary' : 'text-neutral-400'}`}>
                          #
                        </span>
                        <span className="truncate">{ch.name}</span>
                      </span>
                      {ch.badgeCount && (
                        <span className="text-[10px] text-neutral-500 dark:text-neutral-400 font-mono">
                          {ch.badgeCount}
                        </span>
                      )}
                      {ch.hasAlertDot && (
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Usuarios Conectados */}
            <div>
              <div className="px-2 pb-1.5 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                <span>Usuarios Conectados</span>
                <span className="text-[10px] font-mono font-normal">
                  {filteredContacts.filter(c => c.isOnline).length} EN LÍNEA
                </span>
              </div>
              <div className="space-y-1">
                {filteredContacts.map(contact => {
                  const isSelected = selectedContact.id === contact.id;
                  return (
                    <div
                      key={contact.id}
                      onClick={() => handleSelectContact(contact)}
                      className={`w-full text-left p-2.5 rounded-xl border flex items-center justify-between gap-2.5 transition-all cursor-pointer group ${
                        isSelected
                          ? 'bg-white dark:bg-[#131d2e] border-neutral-200/80 dark:border-neutral-800 shadow-sm'
                          : 'border-transparent hover:bg-neutral-200/50 dark:hover:bg-neutral-800/40'
                      }`}
                    >
                      {/* Avatar with Online Ping */}
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="relative shrink-0">
                          <div className={`w-9 h-9 rounded-lg font-bold text-xs flex items-center justify-center ${contact.avatarBgColor}`}>
                            {contact.initials}
                          </div>
                          {contact.isOnline ? (
                            <span className="relative flex h-2.5 w-2.5 absolute -bottom-0.5 -right-0.5">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 ring-2 ring-white dark:ring-[#131d2e]" />
                            </span>
                          ) : (
                            <span className="w-2.5 h-2.5 rounded-full bg-slate-400 absolute -bottom-0.5 -right-0.5 ring-2 ring-white dark:ring-[#131d2e]" />
                          )}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between mb-0.5">
                            <h4 className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                              {contact.name}
                            </h4>
                          </div>
                          <p className="text-[11px] text-neutral-500 dark:text-neutral-400 truncate">
                            {contact.role}
                          </p>
                        </div>
                      </div>

                      {/* Right action / unread */}
                      <div className="flex items-center gap-1.5 shrink-0">
                        {contact.time && (
                          <span className="text-[10px] text-neutral-400 font-mono">
                            {contact.time}
                          </span>
                        )}
                        {contact.unreadCount ? (
                          <span className="px-1.5 py-0.2 text-[9px] font-medium bg-neutral-200 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 rounded-md">
                            {contact.unreadCount}
                          </span>
                        ) : null}
                        
                        {/* Inspect Profile Button (Requirement 3) */}
                        <button
                          type="button"
                          onClick={(e) => handleInspectContact(contact, e)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-neutral-400 hover:text-primary dark:hover:text-indigo-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-all"
                          title="Inspeccionar perfil y credenciales"
                        >
                          <UserCheck className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="p-3 border-t border-neutral-200/60 dark:border-neutral-800/60 bg-white/70 dark:bg-[#111827]/70 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-[11px] text-neutral-600 dark:text-neutral-400 font-medium">
                Nodo Local Sincronizado
              </span>
            </div>
            <span className="text-[10px] font-mono text-neutral-400 dark:text-neutral-500">
              SHA-256 OK
            </span>
          </div>
        </aside>

        {/* RIGHT MAIN CHAT AREA (70-72% width) */}
        <section className={`flex-1 flex flex-col bg-white dark:bg-[#090d16] overflow-hidden ${
          mobileTab === 'chat' ? 'flex' : 'hidden md:flex'
        }`}>
          {/* Main Conversation Header */}
          <div className="h-14 border-b border-neutral-200/80 dark:border-neutral-800/80 px-6 flex items-center justify-between bg-white/80 dark:bg-[#090d16]/80 backdrop-blur-md z-10 shrink-0">
            <div 
              onClick={() => handleInspectContact(selectedContact)}
              className="flex items-center gap-3 cursor-pointer group"
              title="Click para ver credenciales e información del perfil"
            >
              <div className="w-9 h-9 rounded-xl bg-primary/10 dark:bg-primary/20 text-primary font-bold text-xs flex items-center justify-center transition-transform group-hover:scale-105 border border-primary/20">
                {selectedContact.initials}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-neutral-900 dark:text-white group-hover:text-primary dark:group-hover:text-indigo-400 transition-colors">
                    {selectedContact.name}
                  </h2>
                  <span className="text-neutral-400 dark:text-neutral-500 text-xs">—</span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    {selectedContact.role}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                  </span>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                    {selectedContact.isOnline ? 'En línea' : 'Desconectado'}
                  </span>
                  <span className="text-neutral-300 dark:text-neutral-700 text-[10px]">•</span>
                  <span className="text-[11px] text-neutral-400 dark:text-neutral-500">
                    Protección Shield Activa
                  </span>
                </div>
              </div>
            </div>

            {/* Header Right Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleInspectContact(selectedContact)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-100 hover:bg-neutral-200/80 dark:bg-[#141b29] dark:hover:bg-[#1c2638] border border-neutral-200/70 dark:border-neutral-800 text-[11px] text-neutral-700 dark:text-neutral-300 transition-colors"
              >
                <Lock className="w-3.5 h-3.5 text-primary" />
                <span>Canal E2E Enclave Seguro</span>
              </button>
            </div>
          </div>

          {/* Message Stream */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 scroll-smooth">
            {/* Timestamp separator */}
            <div className="flex items-center justify-center">
              <span className="text-[11px] font-mono text-neutral-400 dark:text-neutral-500 bg-neutral-100 dark:bg-[#111827] px-3 py-0.5 rounded-full border border-neutral-200/60 dark:border-neutral-800/80 shadow-xs">
                Hoy, 14:20 UTC • Sesión de Auditoría Iniciada
              </span>
            </div>

            {/* Messages Feed */}
            {messages.map((msg) => {
              if (msg.isCurrentUser) {
                return (
                  <div key={msg.id} className="flex items-start justify-end gap-3 max-w-2xl ml-auto animate-fade-in">
                    <div className="space-y-1 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-[10px] font-mono text-neutral-400">{msg.timestamp}</span>
                        <span className="text-xs font-semibold text-neutral-900 dark:text-white">
                          {msg.senderName}
                        </span>
                      </div>
                      <div className="p-3.5 rounded-2xl rounded-tr-sm bg-primary/10 dark:bg-primary/20 border border-primary/20 text-xs leading-relaxed text-neutral-900 dark:text-neutral-100 text-left shadow-xs">
                        {msg.content}
                      </div>
                      {msg.verifiedDelivery && (
                        <div className="flex items-center justify-end gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
                          <CheckCheck className="w-3.5 h-3.5" />
                          <span>Entregado y Verificado</span>
                        </div>
                      )}
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-primary text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                      {msg.senderInitials || 'OP'}
                    </div>
                  </div>
                );
              }

              // Received message
              return (
                <div key={msg.id} className="flex items-start gap-3 max-w-2xl animate-fade-in">
                  <div 
                    onClick={() => handleInspectContact(selectedContact)}
                    className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5 border border-neutral-200 dark:border-neutral-700 cursor-pointer hover:border-primary transition-colors"
                    title="Click para ver credenciales"
                  >
                    {msg.senderInitials || selectedContact.initials}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-neutral-900 dark:text-white">
                        {msg.senderName}
                      </span>
                      <span className="text-[10px] font-mono text-neutral-400">{msg.timestamp}</span>
                    </div>

                    <div className="p-3.5 rounded-2xl rounded-tl-sm bg-[#FAFAFA] dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800 text-xs leading-relaxed text-neutral-800 dark:text-neutral-200 shadow-xs">
                      {msg.content.includes('[CÉDULA OCULTA]') ? (
                        <>
                          {msg.content.split('[CÉDULA OCULTA]')[0]}
                          <span 
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-mono text-[11px] font-semibold mx-1 cursor-help transition-all hover:bg-amber-500/20"
                            title="Dato de identidad protegido bajo norma de privacidad homomórfica"
                          >
                            <Lock className="w-3 h-3 text-amber-500" />
                            [CÉDULA OCULTA]
                          </span>
                          {msg.content.split('[CÉDULA OCULTA]')[1]}
                        </>
                      ) : (
                        msg.content
                      )}
                    </div>

                    {msg.piiMasked && (
                      <div className="flex items-center gap-2 pl-1 pt-0.5">
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-600 dark:text-emerald-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          PII Sanitizado automáticamente por Shield
                        </span>
                        <span className="text-neutral-300 dark:text-neutral-700 text-[10px]">•</span>
                        <span className="text-[10px] font-mono text-neutral-400">
                          Hash: {msg.piiHash || '89ab...7df1'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* System Audit Notice Card */}
            <div className="p-3 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/70 dark:border-neutral-800/80 max-w-xl mx-auto flex items-center gap-3 text-xs text-neutral-600 dark:text-neutral-400 shadow-xs">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                  Canal Institucional Auditado:
                </span>{' '}
                Todos los mensajes son sellados con hash SHA-256 para trazabilidad ante la Contraloría General.
              </div>
            </div>
          </div>

          {/* Floating Bottom Input Bar */}
          <div className="p-4 border-t border-neutral-200/80 dark:border-neutral-800/80 bg-white/95 dark:bg-[#090d16]/95 shrink-0">
            <form 
              onSubmit={handleSendMessage}
              className="max-w-4xl mx-auto flex items-center gap-2 p-1.5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-[#FAFAFA] dark:bg-[#111827] shadow-sm focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all"
            >
              {/* Paperclip */}
              <button
                type="button"
                className="p-2.5 rounded-xl text-neutral-400 hover:text-neutral-700 dark:text-neutral-500 dark:hover:text-neutral-300 hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 transition-colors"
                title="Adjuntar dictamen o documento"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              {/* Message Input */}
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Escribe un mensaje seguro..."
                className="flex-1 bg-transparent text-xs py-2 px-1 text-neutral-800 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none"
              />

              {/* Quick PII Preset Button */}
              <button
                type="button"
                onClick={handleInsertSamplePII}
                className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20 text-[11px] font-medium hover:bg-amber-500/20 transition-all shrink-0"
                title="Insertar texto de prueba con cédula para probar sanitización"
              >
                <span>+ Probar Cédula</span>
              </button>

              {/* Send Button */}
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-indigo-700 transition-all flex items-center gap-1.5 shadow-sm active:scale-95 shrink-0"
              >
                <span>Enviar</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>

            <div className="mt-2 text-center text-[10px] text-neutral-400 dark:text-neutral-500 font-mono">
              Protección perimetral ISO/IEC 27001 • Cero fugas de información clasificable
            </div>
          </div>
        </section>

      </div>

      {/* Contact Credentials Modal (Requirement 3) */}
      <ContactCredentialsModal
        contact={inspectingContact}
        isOpen={isCredentialsModalOpen}
        onClose={() => setIsCredentialsModalOpen(false)}
        onStartDirectChat={handleSelectContact}
      />
    </div>
  );
};
