import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Search } from 'lucide-react'
import { correlationApi } from '@/api/services'
import MitreTag from '@/components/ui/MitreTag'
import SeverityBadge from '@/components/ui/SeverityBadge'
import { format } from 'date-fns'

export default function Forensics() {
  const [searchIP, setSearchIP] = useState('')
  const [submitted, setSubmitted] = useState('')

  const { data: replayData, isLoading: loadingAlerts } = useQuery({
    queryKey: ['forensicReplay', submitted],
    queryFn: () => correlationApi.getForensicsReplay(submitted),
    enabled: !!submitted,
    refetchInterval: 30_000,
  })

  // The replay API returns chronological alerts
  const timeline = (replayData?.data?.data ?? []).map((a: any) => ({ ts: new Date(a.timestamp), type: 'alert' as const, data: a }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Forensic Timeline</h1>
          <p className="text-aegis-muted text-sm mt-0.5">Reconstruct incident chains from first reconnaissance to deception</p>
        </div>
      </div>

      {/* Search */}
      <form onSubmit={(e) => { e.preventDefault(); setSubmitted(searchIP.trim()) }} className="flex gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-aegis-muted" />
          <input
            value={searchIP}
            onChange={e => setSearchIP(e.target.value)}
            placeholder="Filter by Incident ID"
            className="w-full bg-aegis-surface border border-aegis-border rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-aegis-muted/50 focus:outline-none focus:border-aegis-accent/60 transition-all"
          />
        </div>
        <button type="submit" className="btn-primary px-5 text-sm">Reconstruct</button>
        {submitted && (
          <button type="button" onClick={() => { setSubmitted(''); setSearchIP('') }} className="px-4 py-2 text-xs text-aegis-muted border border-aegis-border rounded-lg hover:text-white transition-colors">
            Clear
          </button>
        )}
      </form>

      {submitted && (
        <div className="text-xs font-mono text-aegis-accent bg-aegis-accent/5 border border-aegis-accent/20 px-4 py-2 rounded-lg">
          Showing forensic timeline for: <strong>{submitted}</strong> — {timeline.length} events reconstructed
        </div>
      )}

      {/* Timeline */}
      {loadingAlerts ? (
        <div className="text-center py-16 text-aegis-muted">Reconstructing incident timeline...</div>
      ) : timeline.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <Search className="w-10 h-10 text-aegis-muted mx-auto mb-3" />
          <p className="text-aegis-muted text-sm">No events found. Enter an attacker IP to reconstruct the incident chain.</p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-aegis-border" />
          <div className="space-y-3">
            <AnimatePresence>
              {timeline.map((event, idx) => (
                <motion.div key={idx} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.03 }}
                  className="relative flex gap-4 pl-14">
                  {/* Dot */}
                  <div className={`absolute left-4 top-3.5 w-4 h-4 rounded-full border-2 flex items-center justify-center ${event.type === 'alert' ? 'border-aegis-danger bg-aegis-danger/20' : 'border-aegis-warn bg-aegis-warn/20'}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                  </div>

                  <div className="glass-card flex-1 p-4 hover:border-aegis-accent/20 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase ${event.type === 'alert' ? 'bg-aegis-danger/10 text-aegis-danger border border-aegis-danger/20' : 'bg-aegis-warn/10 text-aegis-warn border border-aegis-warn/20'}`}>
                          {event.type === 'alert' ? 'THREAT ALERT' : 'HONEYPOT INTERACTION'}
                        </span>
                        {event.type === 'alert' && <SeverityBadge score={(event.data as any).severity_score} />}
                      </div>
                      <span className="text-xs text-aegis-muted font-mono">
                        {format(event.ts, 'HH:mm:ss.SSS')}
                      </span>
                    </div>

                    {event.type === 'alert' && (() => {
                      const a = event.data as any
                      return (
                        <div className="space-y-1 text-xs">
                          <div className="flex gap-4 text-aegis-muted">
                            <span>Attacker: <span className="text-aegis-danger font-mono">{a.attacker_ip}</span></span>
                            <span>Target: <span className="text-slate-300 font-mono">{a.target_ip}</span></span>
                          </div>
                          <div className="flex gap-3 items-center">
                            <span className="text-slate-400">{a.ml_classification.category}</span>
                            {a.mitre_attack && <MitreTag tactic={a.mitre_attack.tactic} technique={a.mitre_attack.technique} />}
                          </div>
                          {a.xai_explanation?.[0] && (
                            <p className="text-aegis-muted italic">"{a.xai_explanation[0]}"</p>
                          )}
                        </div>
                      )
                    })()}

                    {event.type === 'honeypot' && (() => {
                      const h = event.data as any
                      return (
                        <div className="space-y-1 text-xs text-aegis-muted">
                          <div className="flex gap-4">
                            <span>IP: <span className="text-aegis-warn font-mono">{h.attacker_ip}</span></span>
                            <span>Decoy: <span className="text-slate-300">{h.honeypot_type}</span></span>
                          </div>
                          <p>Action: <span className="text-slate-300">{h.interaction_type}</span></p>
                        </div>
                      )
                    })()}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  )
}
