import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { ContactProfile } from '../../../types';

interface ContactListProps {
  contacts: ContactProfile[];
  selectedContactId: string;
  onSelectContact: (id: string) => void;
}

export const ContactList: React.FC<ContactListProps> = ({
  contacts,
  selectedContactId,
  onSelectContact,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = contacts.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs flex flex-col h-[650px] transition-colors">
      {/* Search box */}
      <div className="relative mb-3">
        <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <Search className="w-3.5 h-3.5" />
        </span>
        <input 
          type="text"
          autoComplete="off"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar expediente o contacto..." 
          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-hidden focus:ring-1 focus:ring-[#4f46e5] text-slate-800 dark:text-slate-200 placeholder-slate-400 font-sans"
        />
      </div>

      <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 px-1 font-mono">
        Contactos directos
      </p>

      {/* Contact List */}
      <div className="space-y-1.5 overflow-y-auto flex-1 pr-1">
        {filtered.map((contact) => {
          const isSelected = contact.id === selectedContactId;

          return (
            <div
              key={contact.id}
              onClick={() => onSelectContact(contact.id)}
              className={`flex items-center space-x-3 p-2.5 rounded-xl cursor-pointer transition-colors ${
                isSelected
                  ? 'bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/40'
                  : 'hover:bg-slate-50 dark:hover:bg-slate-800 border border-transparent'
              }`}
            >
              <div className="relative shrink-0">
                <span className={`w-9 h-9 rounded-full font-bold text-xs flex items-center justify-center ${contact.avatarBgColor || 'bg-slate-100 text-slate-700'}`}>
                  {contact.initials}
                </span>
                {contact.isOnline && (
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                  {contact.name}
                </p>
                <p className="text-[11px] text-slate-500 truncate">
                  {contact.role}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
