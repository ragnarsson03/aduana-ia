import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { PasarelaView } from './views/PasarelaView';
import { ChatIAView } from './views/ChatIAView';
import { LedgerView } from './views/LedgerView';
import { ExplicabilidadView } from './views/ExplicabilidadView';
import { CanalSeguroView } from './views/CanalSeguroView';
import { ProfileView } from './views/ProfileView';
import { LoginView } from './views/LoginView';
import { NavTabId } from './types';
import { AuthUser } from './types/auth';
import { MOCK_AUTH_USERS } from './constants/mockAuth';
import { CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => {
    if (typeof window !== 'undefined') {
      const savedRole = localStorage.getItem('aduana_auth_role');
      if (savedRole && MOCK_AUTH_USERS[savedRole]) {
        return MOCK_AUTH_USERS[savedRole];
      }
    }
    return MOCK_AUTH_USERS.auditor; // Default session: Auditora Principal (Deykary González)
  });

  const [activeTab, setActiveTab] = useState<NavTabId>('pasarela');
  const [profileSection, setProfileSection] = useState<'profile' | 'settings'>('profile');
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

  const handleNavigateProfile = (section: 'profile' | 'settings' = 'profile') => {
    setProfileSection(section);
    setActiveTab('perfil');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogin = (user: AuthUser) => {
    setCurrentUser(user);
    localStorage.setItem('aduana_auth_role', user.role);
    setActiveTab('pasarela');
    showNotification(`Bienvenido(a), ${user.name}. Sesión segura iniciada como ${user.roleLabel}.`);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('aduana_auth_role');
    showNotification('Sesión cerrada. Claves efímeras purgadas de memoria confinada.');
  };

  // If no user is logged in, show the sovereign Login view
  if (!currentUser) {
    return (
      <LoginView
        onLogin={handleLogin}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
      />
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#F4F6FB] text-slate-800 dark:bg-[#030712] dark:text-slate-100 transition-colors selection:bg-[#4f46e5] selection:text-white">
      
      {/* Top Header Navbar with User Dropdown */}
      <Navbar
        activeTab={activeTab}
        onTabChange={handleNavigate}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        currentUser={currentUser}
        onLogout={handleLogout}
        onNavigateProfile={handleNavigateProfile}
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
            currentUser={currentUser}
            onBackToPasarela={() => handleNavigate('pasarela')}
            onNotify={showNotification}
            darkMode={darkMode}
            onToggleDarkMode={() => setDarkMode(!darkMode)}
          />
        )}

        {activeTab === 'perfil' && (
          <ProfileView 
            user={currentUser}
            darkMode={darkMode}
            onToggleDarkMode={() => setDarkMode(!darkMode)}
            onLogout={handleLogout}
            onNavigate={handleNavigate}
            defaultSection={profileSection}
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
