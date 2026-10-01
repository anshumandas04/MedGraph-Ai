import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PrototypeNotice } from '../components/PrototypeNotice';
import { 
  LayoutDashboard, Clock, Share2, FileText, Activity, 
  Pill, FlaskConical, Search, BarChart3, Settings, LogOut 
} from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: "/app/dashboard", icon: <LayoutDashboard className="w-5 h-5" />, label: "Overview" },
    { to: "/app/timeline", icon: <Clock className="w-5 h-5" />, label: "Timeline" },
    { to: "/app/graph", icon: <Share2 className="w-5 h-5" />, label: "Knowledge Graph" },
    { to: "/app/documents", icon: <FileText className="w-5 h-5" />, label: "Documents" },
    { to: "/app/signals", icon: <Activity className="w-5 h-5" />, label: "Signals" },
    { to: "/app/medications", icon: <Pill className="w-5 h-5" />, label: "Medications" },
    { to: "/app/investigations", icon: <FlaskConical className="w-5 h-5" />, label: "Investigations" },
    { to: "/app/ask", icon: <Search className="w-5 h-5" />, label: "Ask MedGraph" },
  ];

  if (user?.role === 'ADMIN') {
    navItems.push({ to: "/app/research", icon: <BarChart3 className="w-5 h-5" />, label: "Research Dashboard" });
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <PrototypeNotice />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col">
          <div className="p-4 border-b border-slate-800">
            <h1 className="text-xl font-bold text-white tracking-tight">MedGraph</h1>
            <p className="text-xs text-slate-500 mt-1">Research Prototype v0.1</p>
          </div>
          <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => 
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-primary-600 text-white' 
                      : 'hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-slate-800 space-y-1">
            <NavLink 
              to="/app/settings" 
              className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-slate-800 text-white' : 'hover:bg-slate-800 hover:text-white'}`}
            >
              <Settings className="w-5 h-5" />
              Settings
            </NavLink>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shrink-0">
            <div>
              {/* Context selector could go here */}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-500">Logged in as</span>
              <span className="font-medium text-slate-900">{user?.full_name}</span>
              <span className="bg-slate-100 px-2 py-0.5 rounded text-xs text-slate-600">{user?.role}</span>
            </div>
          </header>
          <div className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
