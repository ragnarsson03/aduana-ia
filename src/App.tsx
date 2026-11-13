import React, { useState, useEffect } from 'react';
import { Navbar, NavTab } from './components/Navbar';
import { Footer } from './components/Footer';
import { LedgerView } from './views/LedgerView';
import { ExplicabilidadView } from './views/ExplicabilidadView';
import { PasarelaView } from './views/PasarelaView';
import { CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('ledger');
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    // Check localStorage or system preference
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

  return (
    <div className="min-h-screen flex flex-col bg-surface text-slate-800 dark:bg-[#0c101d] dark:text-slate-100 transition-colors selection:bg-[#3525cd] selection:text-white">
      
      {/* Top Header Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full animate-in fade-in duration-200">
        {activeTab === 'ledger' && (
          <LedgerView onCopyText={showNotification} />
        )}

        {activeTab === 'explicabilidad' && (
          <ExplicabilidadView onNotify={showNotification} />
        )}

        {activeTab === 'pasarela' && (
          <PasarelaView 
            onNotify={showNotification} 
            onGoToLedger={() => setActiveTab('ledger')}
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
