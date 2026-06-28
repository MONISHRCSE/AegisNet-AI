import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Filter, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { correlationApi } from '@/api/services'
import type { AlertStatus } from '@/types'
import SeverityBadge from '@/components/ui/SeverityBadge'
import MitreTag from '@/components/ui/MitreTag'
import { formatDistanceToNow } from 'date-fns'

export default function Threats() {
  const [selected, setSelected] = useState<any | null>(null)
  const [filter, setFilter]     = useState<string>('all')
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['incidents', filter],
    queryFn: () => correlationApi.listIncidents({ limit: 100 }),
    refetchInterval: 15_000,
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: AlertStatus }) =>
      correlationApi.updateIncidentStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
  })

  const incidents = (data?.data?.data ?? []).filter((i: any) => filter === 'all' || i.status === filter)

  const statusIcon = (s: string) => ({
    open:           <AlertCircle className="w-3 h-3 text-aegis-danger" />,
    investigating:  <Clock className="w-3 h-3 text-aegis-warn" />,
    closed:         <CheckCircle className="w-3 h-3 text-aegis-success" />,
  }[s] || <AlertCircle className="w-3 h-3 text-aegis-danger" />)

  const getScore = (severity: string) => {
    switch(severity) {
      case 'CRITICAL': return 9.0;
      case 'HIGH': return 7.0;
      case 'MEDIUM': return 5.0;
      case 'LOW': return 2.0;
      default: return 1.0;
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Threat Investigation (Incidents)</h1>
        <div className="flex gap-1 bg-aegis-surface border border-aegis-border rounded-lg p-1">
          {['all', 'open', 'investigating', 'closed'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-xs font-medium capitalize transition-colors ${filter === f ? 'bg-aegis-accent text-aegis-bg' : 'text-aegis-muted hover:text-white'}`}>
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-3 glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-aegis-border text-aegis-muted">
                  <th className="text-left px-4 py-3 font-medium">Severity</th>
                  <th className="text-left px-4 py-3 font-medium">Attacker IP</th>
                  <th className="text-left px-4 py-3 font-medium">Attack Chain</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-aegis-border/50">
                <AnimatePresence>
                  {incidents.map((incident: any) => (
                    <motion.tr key={incident.incident_id}
                      initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                      onClick={() => setSelected(incident)}
                      className={`cursor-pointer hover:bg-aegis-card/60 transition-colors ${selected?.incident_id === incident.incident_id ? 'bg-aegis-accent/5 border-l-2 border-l-aegis-accent' : ''}`}>
                      <td className="px-4 py-2.5"><SeverityBadge score={getScore(incident.severity)} /></td>
                      <td className="px-4 py-2.5 font-mono text-slate-300">{incident.attacker_ip}</td>
                      <td className="px-4 py-2.5 text-slate-400">
                        {incident.attack_chain.length > 0 ? incident.attack_chain.join(' → ') : 'Unknown'}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">{statusIcon(incident.status)}<span className="capitalize text-aegis-muted">{incident.status}</span></div>
                      </td>
                      <td className="px-4 py-2.5 text-aegis-muted">
                        {formatDistanceToNow(new Date(incident.last_updated), { addSuffix: true })}
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
            {isLoading && <div className="text-center py-8 text-aegis-muted text-sm">Loading incidents...</div>}
            {!isLoading && incidents.length === 0 && <div className="text-center py-8 text-aegis-muted text-sm">No incidents match the current filter.</div>}
          </div>
        </div>

        <div className="xl:col-span-2">
          {selected ? (
            <div className="glass-card p-6 h-full space-y-4">
              <h2 className="text-lg font-bold text-white">Incident Profile</h2>
              <div className="space-y-2">
                <p className="text-xs text-aegis-muted">Incident ID: <span className="font-mono text-white">{selected.incident_id}</span></p>
                <p className="text-xs text-aegis-muted">Attacker IP: <span className="font-mono text-aegis-danger">{selected.attacker_ip}</span></p>
                <p className="text-xs text-aegis-muted">Honeypot Interactions: <span className="font-mono text-aegis-warn">{selected.honeypot_interactions}</span></p>
                <p className="text-xs text-aegis-muted">Total Alerts Merged: <span className="font-mono text-white">{selected.alert_ids.length}</span></p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-aegis-muted font-bold">MITRE Progression:</p>
                <div className="flex flex-wrap gap-2">
                  {selected.mitre_tactics.map((m: any, idx: number) => (
                    <MitreTag key={idx} tactic={m.tactic} technique={m.technique} />
                  ))}
                </div>
              </div>
              <div className="pt-4 border-t border-aegis-border">
                <button onClick={() => updateStatus.mutate({ id: selected.incident_id, status: selected.status === 'open' ? 'closed' : 'open' as AlertStatus })} className="btn-secondary w-full">
                  Toggle Status ({selected.status})
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-card p-8 flex flex-col items-center justify-center text-center h-64">
              <Filter className="w-8 h-8 text-aegis-muted mb-3" />
              <p className="text-aegis-muted text-sm">Select an incident to view profile</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
