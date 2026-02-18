
import React, { useState, createContext, useContext } from 'react';
import { HashRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Monitor, 
  ShieldAlert, 
  BrainCircuit, 
  Settings as SettingsIcon, 
  LogOut,
  Bell,
  Search,
  FileBarChart,
  Building2,
  Globe,
  ShieldCheck,
  Code
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import Alerts from './pages/Alerts';
import AIInsights from './pages/AIInsights';
import Reports from './pages/Reports';
import AgentSource from './pages/AgentSource';
import Settings from './pages/Settings';
import { translations } from './translations';

type Language = 'en' | 'ar';
const LanguageContext = createContext({
  lang: 'en' as Language,
  setLang: (l: Language) => {},
  t: (key: keyof typeof translations['en']) => ''
});

export const useTranslation = () => useContext(LanguageContext);

const SidebarItem: React.FC<{ 
  icon: React.ReactNode; 
  label: string; 
  to: string; 
  active?: boolean;
  rtl?: boolean;
}> = ({ icon, label, to, active, rtl }) => (
  <Link
    to={to}
    className={`flex items-center justify-between group px-4 py-3 rounded-xl transition-all duration-300 ${
      active 
        ? 'bg-emerald-500 text-zinc-950 font-bold shadow-lg shadow-emerald-500/20' 
        : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100'
    } ${rtl ? 'flex-row-reverse' : 'flex-row'}`}
  >
    <div className={`flex items-center gap-3 ${rtl ? 'flex-row-reverse' : 'flex-row'}`}>
      {icon}
      <span className="text-sm tracking-tight">{label}</span>
    </div>
    {active && <div className="w-1.5 h-1.5 bg-zinc-950 rounded-full animate-pulse" />}
  </Link>
);

const App: React.FC = () => {
  const [lang, setLang] = useState<Language>('en');
  const t = (key: keyof typeof translations['en']) => translations[lang][key] || key;
  const isRtl = lang === 'ar';

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      <HashRouter>
        <div className={`flex min-h-screen ${isRtl ? 'flex-row-reverse' : 'flex-row'}`} dir={isRtl ? 'rtl' : 'ltr'}>
          {/* Modern Sidebar */}
          <aside className={`w-72 border-zinc-800/50 flex flex-col fixed inset-y-0 bg-zinc-950/40 backdrop-blur-2xl z-50 ${isRtl ? 'border-l left-auto right-0' : 'border-r'}`}>
            <div className="p-8">
              <div className={`flex items-center gap-3 mb-10 ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
                  <ShieldCheck className="w-6 h-6 text-zinc-950" />
                </div>
                <div className={isRtl ? 'text-right' : 'text-left'}>
                  <h1 className="text-xl font-extrabold tracking-tighter text-zinc-100 leading-none">IVECGUARD</h1>
                  <span className="text-[10px] font-black text-emerald-500 tracking-[0.2em] uppercase opacity-80">AI PRO OPS</span>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <p className={`px-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-4 ${isRtl ? 'text-right' : 'text-left'}`}>
                    {lang === 'en' ? 'COMMAND CENTER' : 'مركز القيادة'}
                  </p>
                  <nav className="space-y-1">
                    <SidebarNavigation rtl={isRtl} />
                  </nav>
                </div>
              </div>
            </div>

            <div className="mt-auto p-6 space-y-4">
              <button 
                onClick={() => setLang(lang === 'en' ? 'ar' : 'en')}
                className={`w-full flex items-center gap-3 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-xs font-bold transition-all hover:bg-zinc-800 ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <Globe className="w-4 h-4 text-emerald-500" />
                <span>{lang === 'en' ? 'العربية' : 'English'}</span>
              </button>

              <div className="p-4 glass rounded-2xl border border-emerald-500/10">
                <div className={`flex items-center gap-2 mb-2 ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                  <Building2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold text-zinc-200">Global Dynamics</span>
                </div>
                <p className={`text-[10px] text-zinc-500 mb-3 ${isRtl ? 'text-right' : 'text-left'}`}>{t('autoReg')}</p>
                <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 w-full animate-pulse" />
                </div>
              </div>
              
              <button className={`w-full flex items-center gap-3 px-4 py-3 text-zinc-500 hover:text-rose-400 transition-colors ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                <LogOut className="w-5 h-5" />
                <span className="text-sm font-bold uppercase tracking-wider">{lang === 'en' ? 'DEAUTHORIZE' : 'تسجيل الخروج'}</span>
              </button>
            </div>
          </aside>

          {/* Dynamic Header & Content */}
          <main className={`flex-1 flex flex-col relative ${isRtl ? 'mr-72 ml-0' : 'ml-72 mr-0'}`}>
            <header className={`h-20 flex items-center justify-between px-10 bg-zinc-950/20 backdrop-blur-sm sticky top-0 z-40 border-b border-zinc-800/30 ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className="relative group w-80">
                <Search className={`absolute ${isRtl ? 'right-4' : 'left-4'} top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-emerald-500 transition-colors`} />
                <input 
                  type="text" 
                  placeholder={t('search')}
                  className={`w-full bg-zinc-900/50 border border-zinc-800/50 rounded-2xl py-2.5 ${isRtl ? 'pr-12 pl-4 text-right' : 'pl-12 pr-4 text-left'} text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:bg-zinc-900 transition-all placeholder:text-zinc-600`}
                />
              </div>

              <div className={`flex items-center gap-6 ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex items-center gap-4 ${isRtl ? 'border-l pl-6 border-zinc-800 flex-row-reverse' : 'border-r pr-6 border-zinc-800 flex-row'}`}>
                   <div className={isRtl ? 'text-left' : 'text-right'}>
                     <div className="text-[10px] font-black text-rose-500 animate-pulse tracking-widest mb-0.5">PRIORITY 1</div>
                     <div className="text-xs font-bold text-zinc-400">3 Alerts Pending</div>
                   </div>
                   <button className="w-10 h-10 glass rounded-full flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition-all">
                     <Bell className="w-5 h-5" />
                   </button>
                </div>
                
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 p-0.5 shadow-lg">
                  <div className="w-full h-full bg-zinc-900 rounded-[10px] overflow-hidden">
                    <img src="https://api.dicebear.com/7.x/shapes/svg?seed=admin" alt="Avatar" />
                  </div>
                </div>
              </div>
            </header>

            <div className="p-10">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/devices" element={<Devices />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/ai-insights" element={<AIInsights />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/deploy" element={<AgentSource />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </main>
        </div>
      </HashRouter>
    </LanguageContext.Provider>
  );
};

const SidebarNavigation: React.FC<{ rtl: boolean }> = ({ rtl }) => {
  const location = useLocation();
  const { t } = useTranslation();
  return (
    <>
      <SidebarItem icon={<LayoutDashboard className="w-4 h-4" />} label={t('dashboard')} to="/" active={location.pathname === '/'} rtl={rtl} />
      <SidebarItem icon={<Monitor className="w-4 h-4" />} label={t('agents')} to="/devices" active={location.pathname === '/devices'} rtl={rtl} />
      <SidebarItem icon={<ShieldAlert className="w-4 h-4" />} label={t('logs')} to="/alerts" active={location.pathname === '/alerts'} rtl={rtl} />
      <SidebarItem icon={<BrainCircuit className="w-4 h-4" />} label={t('intelligence')} to="/ai-insights" active={location.pathname === '/ai-insights'} rtl={rtl} />
      <SidebarItem icon={<FileBarChart className="w-4 h-4" />} label={t('compliance')} to="/reports" active={location.pathname === '/reports'} rtl={rtl} />
      <SidebarItem icon={<SettingsIcon className="w-4 h-4" />} label="Governance" to="/settings" active={location.pathname === '/settings'} rtl={rtl} />
      <SidebarItem icon={<Code className="w-4 h-4" />} label="Deploy Source" to="/deploy" active={location.pathname === '/deploy'} rtl={rtl} />
    </>
  );
};

export default App;
