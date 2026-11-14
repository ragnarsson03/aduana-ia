import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { PasarelaView } from './views/PasarelaView';
import { ChatIAView } from './views/ChatIAView';
import { LedgerView } from './views/LedgerView';
import { ExplicabilidadView } from './views/ExplicabilidadView';
import { CanalSeguroView } from './views/CanalSeguroView';
import { NavTabId } from './types';
import { CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>('pasarela');
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('aduana_dark_mode');
      if (saved !== null) return saved === 'true';
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Sync dark class on documentElement
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('aduana_dark_mode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('aduana_dark_mode', 'false');
    }
  }, [darkMode]);

  const showNotification = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 3500);
  };

  const handleNavigate = (tab: NavTabId) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F4F6FB] text-slate-800 dark:bg-[#030712] dark:text-slate-100 transition-colors selection:bg-[#4f46e5] selection:text-white">
      
      {/* Top Header Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={handleNavigate}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full animate-in fade-in duration-200">
        {activeTab === 'pasarela' && (
          <PasarelaView 
            onNavigateToLedger={() => handleNavigate('ledger')}
            onNavigateToExplica={() => handleNavigate('explicabilidad')}
            onNotify={showNotification}
          />
        )}

        {activeTab === 'chat' && (
          <ChatIAView 
            onNotify={showNotification}
            onNavigateToLedger={() => handleNavigate('ledger')}
            onNavigateToExplica={() => handleNavigate('explicabilidad')}
          />
        )}

        {activeTab === 'ledger' && (
          <LedgerView onCopyText={showNotification} />
        )}

        {activeTab === 'explicabilidad' && (
          <ExplicabilidadView onNotify={showNotification} />
        )}

        {activeTab === 'canal' && (
          <CanalSeguroView 
            onBackToPasarela={() => handleNavigate('pasarela')}
            onNotify={showNotification}
          />
        )}
      </main>

      {/* Global Page Footer */}
      <Footer />

      {/* Floating Sovereign Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-3 fade-in duration-200 max-w-md">
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xl border border-slate-700 dark:border-slate-200 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 dark:text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
        </div>
      )}

    </div>
  );
};

export default App;
