import React, { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Terminal, Shield } from 'lucide-react'
import { telemetryApi } from '@/api/services'
import { useAlertStore } from '@/stores/alertStore'
import { formatDistanceToNow } from 'date-fns'

export default function Honeypots() {
  const terminalRef = useRef<HTMLDivElement>(null)
  const { data, refetch } = useQuery({
    queryKey: ['honeypotLogs'],
    queryFn: () => telemetryApi.honeypotLogs({ limit: 100 }),
    refetchInterval: 5_000,
  })
  const logs = data?.data ?? []

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs])

  const interactionColor = (type: string) => {
    if (type.includes('login'))   return 'text-aegis-danger'
    if (type.includes('command')) return 'text-aegis-warn'
    if (type.includes('connect')) return 'text-aegis-accent'
    return 'text-aegis-success'
  }

  const formatPayload = (payload: Record<string, unknown>) => {
    const parts = Object.entries(payload)
      .filter(([k]) => k !== 'success')
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    return parts.join(' ')
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Honeypot Activity Console</h1>
          <p className="text-aegis-muted text-sm mt-0.5">Live attacker interaction stream from decoy services</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-aegis-danger bg-aegis-danger/10 px-3 py-1.5 rounded-full border border-aegis-danger/20">
          <span className="w-1.5 h-1.5 bg-aegis-danger rounded-full animate-pulse" />
          {logs.length} INTERACTIONS LOGGED
        </div>
      </div>

      {/* Terminal */}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-aegis-border bg-aegis-surface">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-aegis-danger/60" />
            <span className="w-3 h-3 rounded-full bg-aegis-warn/60" />
            <span className="w-3 h-3 rounded-full bg-aegis-success/60" />
          </div>
          <div className="flex items-center gap-2 ml-2">
            <Terminal className="w-3.5 h-3.5 text-aegis-muted" />
            <span className="text-xs font-mono text-aegis-muted">aegisnet-honeypot-console</span>
          </div>
        </div>

        <div
          ref={terminalRef}
          className="h-[500px] overflow-y-auto p-4 font-mono text-xs space-y-1 bg-[#050810]"
        >
          {logs.length === 0 && (
            <p className="text-aegis-muted animate-pulse">Waiting for attacker interactions...</p>
          )}
          <AnimatePresence initial={false}>
            {[...logs].reverse().map((log, i) => (
              <motion.div
                key={log._id || i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-3 leading-relaxed hover:bg-aegis-card/30 px-1 rounded"
              >
                <span className="text-aegis-muted shrink-0 select-none">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-aegis-accent shrink-0">[{log.honeypot_type}]</span>
                <span className="text-slate-500 shrink-0">{log.attacker_ip}</span>
                <span className={`shrink-0 ${interactionColor(log.interaction_type)}`}>
                  {log.interaction_type}
                </span>
                <span className="text-slate-400 truncate">{formatPayload(log.payload)}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Session Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['ssh-cowrie', 'mysql-fake', 'http-admin-fake'].map(type => {
          const typeLogs = logs.filter(l => l.honeypot_type === type)
          return (
            <div key={type} className="glass-card p-4">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-aegis-warn" />
                <span className="text-sm font-medium text-white">{type}</span>
              </div>
              <div className="space-y-1 text-xs text-aegis-muted">
                <div className="flex justify-between"><span>Interactions</span><span className="text-slate-300">{typeLogs.length}</span></div>
                <div className="flex justify-between"><span>Unique IPs</span><span className="text-slate-300">{new Set(typeLogs.map(l => l.attacker_ip)).size}</span></div>
                <div className="flex justify-between"><span>Last Activity</span>
                  <span className="text-slate-300">
                    {typeLogs[0] ? formatDistanceToNow(new Date(typeLogs[0].timestamp), { addSuffix: true }) : 'None'}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
