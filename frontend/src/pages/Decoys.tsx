import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Server, StopCircle } from 'lucide-react'
import { honeypotApi, correlationApi } from '@/api/services'
import { useAuthStore } from '@/stores/authStore'
import { formatDistanceToNow } from 'date-fns'

export default function Decoys() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'Admin'

  const { data, isLoading } = useQuery({ queryKey: ['decoys'], queryFn: () => honeypotApi.decoys(), refetchInterval: 10_000 })
  const { data: corrDecoyData } = useQuery({ queryKey: ['activeDecoysCorr'], queryFn: () => correlationApi.getActiveDecoys(), refetchInterval: 10_000 })
  const terminate = useMutation({ mutationFn: (id: string) => honeypotApi.terminate(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['decoys'] }) })

  const decoys = data?.data ?? []
  // Merge correlation engine decoys (may have attacker session data)
  const corrDecoys: any[] = corrDecoyData?.data?.data ?? []
  const active  = decoys.filter((d: any) => d.status === 'running')
  const stopped = decoys.filter((d: any) => d.status !== 'running')

  const statusColor = (s: string) => ({ running: 'text-aegis-success bg-aegis-success/10 border-aegis-success/30', pending: 'text-aegis-warn bg-aegis-warn/10 border-aegis-warn/30', stopped: 'text-aegis-muted bg-aegis-muted/10 border-aegis-muted/30', archived: 'text-aegis-muted bg-aegis-muted/10 border-aegis-muted/30' }[s] ?? 'text-aegis-muted')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Decoy Management</h1>
        <div className="flex gap-3">
          <span className="px-3 py-1 bg-aegis-success/10 text-aegis-success border border-aegis-success/20 rounded-full text-xs font-mono">{active.length} ACTIVE</span>
          <span className="px-3 py-1 bg-aegis-muted/10 text-aegis-muted border border-aegis-border rounded-full text-xs font-mono">{stopped.length} INACTIVE</span>
        </div>
      </div>

      {isLoading && <p className="text-center text-aegis-muted py-10">Loading decoys...</p>}

      {active.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-aegis-muted mb-3 uppercase tracking-widest">Active Decoys</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {active.map(decoy => (
              <motion.div key={decoy.id} layout initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
                className="glass-card p-5 border border-aegis-success/20 hover:border-aegis-success/40 transition-all">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-aegis-success/10 rounded-lg"><Server className="w-4 h-4 text-aegis-success" /></div>
                    <div>
                      <p className="text-sm font-semibold text-white font-mono">{decoy.template?.name ?? 'Unknown'}</p>
                      <p className="text-xs text-aegis-muted">{decoy.assigned_ip}</p>
                    </div>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${statusColor(decoy.status)}`}>{decoy.status.toUpperCase()}</span>
                </div>
                <div className="space-y-1.5 text-xs text-aegis-muted">
                  <div className="flex justify-between"><span>Target Attacker</span><span className="font-mono text-aegis-danger">{decoy.target_attacker_ip}</span></div>
                  <div className="flex justify-between"><span>Deployed</span><span className="text-slate-400">{formatDistanceToNow(new Date(decoy.created_at), { addSuffix: true })}</span></div>
                </div>
                {isAdmin && (
                  <button onClick={() => terminate.mutate(decoy.id)} disabled={terminate.isPending}
                    className="btn-danger w-full mt-4 text-xs py-2 flex items-center justify-center gap-2">
                    <StopCircle className="w-3.5 h-3.5" /> Terminate Decoy
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {stopped.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-aegis-muted mb-3 uppercase tracking-widest">Deployment History</h2>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-aegis-border text-aegis-muted">
                <th className="text-left px-4 py-3">Template</th>
                <th className="text-left px-4 py-3">Attacker IP</th>
                <th className="text-left px-4 py-3">Deployed</th>
                <th className="text-left px-4 py-3">Status</th>
              </tr></thead>
              <tbody className="divide-y divide-aegis-border/50">
                {stopped.map(d => (
                  <tr key={d.id} className="text-slate-400">
                    <td className="px-4 py-2.5">{d.template?.name ?? '—'}</td>
                    <td className="px-4 py-2.5 font-mono">{d.target_attacker_ip}</td>
                    <td className="px-4 py-2.5">{formatDistanceToNow(new Date(d.created_at), { addSuffix: true })}</td>
                    <td className="px-4 py-2.5"><span className={`px-2 py-0.5 rounded border text-[10px] ${statusColor(d.status)}`}>{d.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!isLoading && decoys.length === 0 && (
        <div className="glass-card p-16 text-center">
          <Server className="w-10 h-10 text-aegis-muted mx-auto mb-3" />
          <p className="text-aegis-muted text-sm">No decoys deployed. They are provisioned automatically when threats are detected.</p>
        </div>
      )}
    </div>
  )
}
