import os

project_root = r"C:\Users\anshu\.gemini\antigravity\scratch\medgraph\frontend"

files = {
    "package.json": """{
  "name": "medgraph-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "@tanstack/react-query": "^5.62.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^3.9.1",
    "zod": "^3.24.0",
    "axios": "^1.7.9",
    "recharts": "^2.14.0",
    "lucide-react": "^0.460.0",
    "date-fns": "^4.1.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.5"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.6.3",
    "vite": "^6.0.3",
    "vitest": "^2.1.8",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "jsdom": "^25.0.1"
  }
}""",
    "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}""",
    "tsconfig.node.json": """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}""",
    "vite.config.ts": """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
      }
    },
  },
  plugins: [],
}""",
    "postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
    "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MedGraph — Healthcare Journey Reconstruction</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body class="bg-slate-50 text-slate-900 antialiased font-sans">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>""",
    "src/main.tsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import AppRoutes from './routes';
import { AuthProvider } from './hooks/useAuth';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);""",
    "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    font-family: 'Inter', sans-serif;
  }
}""",
    "src/types/index.ts": """export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'RESEARCHER' | 'CLINICIAN';
}
export interface PatientSummary {
  id: string;
  name: string;
  dob: string;
}
export interface DocumentDetail {
  id: string;
  filename: string;
  status: string;
}
export interface TimelineEntry {
  id: string;
  date: string;
  type: string;
  description: string;
}
export interface SignalResponse {
  id: string;
  type: string;
  severity: string;
}
export interface ErrorResponse {
  message: string;
}
""",
    "src/hooks/useAuth.tsx": """import React, { createContext, useContext, useState, ReactNode } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = (token: string, u: User) => {
    localStorage.setItem('token', token);
    setUser(u);
  };
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};""",
    "src/layouts/AppLayout.tsx": """import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LayoutDashboard, Clock, FileText, AlertTriangle, GitBranch, Pill, TestTube, MessageSquare, Settings, LogOut, BarChart3 } from 'lucide-react';
import PrototypeNotice from '../components/PrototypeNotice';

export default function AppLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 shrink-0">
        <div className="font-bold text-xl text-primary-600">MedGraph</div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">{user?.full_name}</span>
          <button onClick={logout} className="p-2 text-slate-500 hover:text-slate-700">
            <LogOut size={20} />
          </button>
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-white border-r border-slate-200 flex flex-col py-4 overflow-y-auto">
          <nav className="flex-1 space-y-1 px-3">
            <Link to="/app/dashboard" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><LayoutDashboard size={18} /> Dashboard</Link>
            <Link to="/app/timeline" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><Clock size={18} /> Timeline</Link>
            <Link to="/app/graph" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><GitBranch size={18} /> Graph</Link>
            <Link to="/app/documents" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><FileText size={18} /> Documents</Link>
            <Link to="/app/signals" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><AlertTriangle size={18} /> Signals</Link>
            <Link to="/app/medications" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><Pill size={18} /> Medications</Link>
            <Link to="/app/investigations" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><TestTube size={18} /> Investigations</Link>
            <Link to="/app/ask" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><MessageSquare size={18} /> Ask MedGraph</Link>
            <Link to="/app/settings" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><Settings size={18} /> Settings</Link>
            {user?.role === 'ADMIN' && (
              <>
                <div className="my-2 border-t border-slate-200"></div>
                <Link to="/app/research" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-100"><BarChart3 size={18} /> Research</Link>
              </>
            )}
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50 flex flex-col">
          <PrototypeNotice />
          <div className="flex-1 mt-4">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}""",
    "src/components/PrototypeNotice.tsx": """import React from 'react';
export default function PrototypeNotice() {
  return (
    <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-md text-sm font-medium text-center">
      Research prototype — Synthetic data only — Not for medical decisions
    </div>
  );
}""",
    "src/routes/index.tsx": """import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import { useAuth } from '../hooks/useAuth';

// Mock components for pages
const Landing = () => <div className="p-10 flex flex-col items-center">
  <h1 className="text-4xl font-bold mb-4 text-primary-600">MEDGRAPH</h1>
  <p className="text-xl mb-8">Don't just store the medical record. Understand what happened next.</p>
  <a href="/login" className="bg-primary-600 text-white px-6 py-2 rounded-md font-medium">Explore Demo</a>
</div>;
const Login = () => <div className="flex min-h-screen items-center justify-center p-4">
  <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
    <h2 className="text-2xl font-bold mb-6">Login</h2>
    <a href="/app/dashboard" className="block w-full bg-primary-600 text-white text-center py-2 rounded">Bypass Login (Demo)</a>
  </div>
</div>;
const Dashboard = () => <div>Dashboard Content</div>;
const Timeline = () => <div>Timeline Content</div>;
const Graph = () => <div>Graph Content</div>;
const Documents = () => <div>Documents Content</div>;
const Signals = () => <div>Signals Content</div>;
const Medications = () => <div>Medications Content</div>;
const Investigations = () => <div>Investigations Content</div>;
const Ask = () => <div>Ask MedGraph Content</div>;
const Settings = () => <div>Settings Content</div>;
const NotFound = () => <div>404 - Not Found</div>;

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<div>Register</div>} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<Navigate to="dashboard" />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="timeline" element={<Timeline />} />
        <Route path="graph" element={<Graph />} />
        <Route path="documents" element={<Documents />} />
        <Route path="signals" element={<Signals />} />
        <Route path="medications" element={<Medications />} />
        <Route path="investigations" element={<Investigations />} />
        <Route path="ask" element={<Ask />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}""",
    "Dockerfile": """FROM node:22-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]""",
    "nginx.conf": """server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}"""
}

for rel_path, content in files.items():
    full_path = os.path.join(project_root, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Created {len(files)} files successfully in {project_root}")
