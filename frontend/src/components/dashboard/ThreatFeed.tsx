import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { SecurityAlert } from '@/types'
import SeverityBadge from '@/components/ui/SeverityBadge'
import MitreTag from '@/components/ui/MitreTag'
import { formatDistanceToNow } from 'date-fns'

interface Props { alerts: SecurityAlert[] }

export default function ThreatFeed({ alerts }: Props) {
  return (
    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
      <AnimatePresence initial={false}>
        {alerts.slice(0, 30).map((alert, idx) => (
          <motion.div key={alert._alert_id || idx}
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex items-center gap-3 p-2.5 bg-aegis-bg/60 rounded-lg border border-aegis-border/50 hover:border-aegis-accent/20 transition-colors"
          >
            <SeverityBadge score={alert.severity_score} />
            <span className="font-mono text-xs text-aegis-danger flex-shrink-0">{alert.attacker_ip}</span>
            <span className="text-xs text-slate-400 flex-1 truncate">{alert.ml_classification.category}</span>
            {alert.mitre_attack && <MitreTag tactic={alert.mitre_attack.tactic} technique={alert.mitre_attack.technique} />}
            <span className="text-[10px] text-aegis-muted flex-shrink-0">
              {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>
      {alerts.length === 0 && <p className="text-center text-aegis-muted text-xs py-8">No live alerts — system is quiet.</p>}
    </div>
  )
}
