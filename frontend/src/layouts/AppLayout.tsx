import React from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Activity, Network, AlertTriangle, Bug, Server, Search, LogOut, Bell } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useAlertStore } from '@/stores/alertStore'
import clsx from 'clsx'

const NAV_ITEMS = [
  { to: '/',          icon: Activity,      label: 'Overview'   },
  { to: '/topology',  icon: Network,       label: 'Topology'   },
  { to: '/threats',   icon: AlertTriangle, label: 'Threats'    },
  { to: '/honeypots', icon: Bug,           label: 'Honeypots'  },
  { to: '/decoys',    icon: Server,        label: 'Decoys'     },
  { to: '/forensics', icon: Search,        label: 'Forensics'  },
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout }              = useAuthStore()
  const { unreadCount, clearUnread }  = useAlertStore()
  const navigate                      = useNavigate()
  const { pathname }                  = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-aegis-bg">
      {/* ── Sidebar ───────────────────────────────────────── */}
      <aside className="w-16 lg:w-56 flex flex-col bg-aegis-surface border-r border-aegis-border shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-aegis-border">
          <div className="relative">
            <Shield className="w-7 h-7 text-aegis-accent" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-aegis-accent rounded-full animate-ping" />
          </div>
          <span className="hidden lg:block font-bold text-white text-sm tracking-widest">AEGISNET</span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-aegis-accent/10 text-aegis-accent border border-aegis-accent/20'
                  : 'text-slate-400 hover:text-white hover:bg-aegis-card'
              )}>
              <Icon className="w-4 h-4 shrink-0" />
              <span className="hidden lg:block">{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User info + logout */}
        <div className="px-2 py-4 border-t border-aegis-border space-y-1">
          <div className="hidden lg:block px-3 py-2 text-xs text-aegis-muted">
            <span className="font-medium text-slate-300">{user?.username ?? 'Guest'}</span>
            {user?.role && (
              <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-aegis-accent/10 text-aegis-accent rounded">
                {user.role}
              </span>
            )}
          </div>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-aegis-danger hover:bg-aegis-danger/10 transition-all"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            <span className="hidden lg:block">Logout</span>
          </button>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between px-6 py-3 bg-aegis-surface border-b border-aegis-border">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-aegis-success rounded-full animate-pulse" />
            <span className="text-xs text-aegis-muted font-mono">LIVE MONITORING</span>
          </div>
          <button onClick={clearUnread} className="relative p-2 rounded-lg hover:bg-aegis-card transition-colors">
            <Bell className="w-4 h-4 text-slate-400" />
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0 }} animate={{ scale: 1 }}
                className="absolute -top-0.5 -right-0.5 w-4 h-4 flex items-center justify-center text-[9px] font-bold bg-aegis-danger text-white rounded-full"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </motion.span>
            )}
          </button>
        </header>

        {/* Page */}
        <main className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
