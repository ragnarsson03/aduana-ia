import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { ContactProfile } from '../../../types';

interface ContactDirectoryProps {
  contacts: ContactProfile[];
  selectedContactId: string;
  onSelectContact: (id: string) => void;
}

export const ContactDirectory: React.FC<ContactDirectoryProps> = ({
  contacts,
  selectedContactId,
  onSelectContact,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = contacts.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-xs flex flex-col h-[650px] transition-colors">
      
      {/* Search box with pill/rounded style matching screenshot */}
      <div className="relative mb-4">
        <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <Search className="w-3.5 h-3.5" />
        </span>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar"
          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/80 focus:outline-hidden focus:ring-1 focus:ring-[#4f46e5] text-slate-800 dark:text-slate-200 placeholder-slate-400 font-sans transition-all"
        />
      </div>

      {/* Eyebrow / Label */}
      <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-3 px-1">
        Contacto directos
      </p>

      {/* Scrollable contact items list */}
      <div className="space-y-1.5 overflow-y-auto flex-1 pr-1">
        {filtered.map((contact, idx) => {
          const isSelected = contact.id === selectedContactId || (selectedContactId === 'c1' && idx === 0);

          return (
            <div
              key={`${contact.id}-${idx}`}
              onClick={() => onSelectContact(contact.id)}
              className={`flex items-center space-x-3 p-2.5 rounded-2xl cursor-pointer transition-all ${
                isSelected
                  ? 'bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-800/60 shadow-2xs'
                  : 'hover:bg-slate-50 dark:hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              {/* Circular Avatar with status dot */}
              <div className="relative shrink-0">
                <span className={`w-9 h-9 rounded-full font-bold text-[11px] flex items-center justify-center select-none ${contact.avatarBgColor || 'bg-slate-100 text-slate-700'}`}>
                  {contact.initials}
                </span>
                {contact.isOnline && (
                  <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" />
                )}
              </div>

              {/* Name & Role */}
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5 truncate">
                  <span>{contact.name}</span>
                  {contact.hasGreenDot && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  )}
                </p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate mt-0.5 font-normal">
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
