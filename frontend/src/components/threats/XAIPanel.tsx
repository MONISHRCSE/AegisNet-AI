import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Target, ChevronDown, ChevronUp, CheckCircle, Clock } from 'lucide-react'
import type { SecurityAlert, AlertStatus } from '@/types'
import SeverityBadge from '@/components/ui/SeverityBadge'
import MitreTag from '@/components/ui/MitreTag'
import { format } from 'date-fns'

interface Props { alert: SecurityAlert; onUpdateStatus: (status: AlertStatus) => void }

export default function XAIPanel({ alert, onUpdateStatus }: Props) {
  const confidencePct = Math.round(alert.ml_classification.confidence * 100)

  return (
    <motion.div key={alert._alert_id} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }}
      className="glass-card p-5 space-y-5 h-fit sticky top-0">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-aegis-muted font-mono mb-1">{alert._alert_id?.slice(0, 16)}...</p>
          <SeverityBadge score={alert.severity_score} />
        </div>
        <p className="text-xs text-aegis-muted">{format(new Date(alert.timestamp), 'HH:mm:ss dd/MM')}</p>
      </div>

      {/* IPs */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-aegis-bg rounded-lg p-3 border border-aegis-border">
          <p className="text-aegis-muted mb-1">Attacker</p>
          <p className="font-mono text-aegis-danger">{alert.attacker_ip}</p>
        </div>
        <div className="bg-aegis-bg rounded-lg p-3 border border-aegis-border">
          <p className="text-aegis-muted mb-1">Target</p>
          <p className="font-mono text-slate-300">{alert.target_ip}</p>
        </div>
      </div>

      {/* ML Model Output */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-aegis-accent uppercase tracking-widest flex items-center gap-1.5">
          <Brain className="w-3.5 h-3.5" /> ML Analysis
        </p>
        <div className="bg-aegis-bg rounded-lg p-3 border border-aegis-border space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-aegis-muted">Category</span>
            <span className="text-white font-medium">{alert.ml_classification.category}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-aegis-muted">Confidence</span>
            <div className="flex items-center gap-2">
              <div className="w-20 bg-aegis-border rounded-full h-1.5">
                <div className="h-1.5 rounded-full bg-aegis-accent" style={{ width: `${confidencePct}%` }} />
              </div>
              <span className="text-slate-300 w-8 text-right">{confidencePct}%</span>
            </div>
          </div>
          <div className="flex justify-between">
            <span className="text-aegis-muted">Anomaly Score</span>
            <span className="font-mono text-aegis-warn">{alert.anomaly_score.toFixed(4)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-aegis-muted">Model</span>
            <span className="text-slate-400 text-[10px]">{alert.ml_classification.model}</span>
          </div>
        </div>
      </div>

      {/* MITRE */}
      {alert.mitre_attack && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-aegis-muted uppercase tracking-widest flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5" /> MITRE ATT&CK
          </p>
          <div className="bg-aegis-bg rounded-lg p-3 border border-purple-900/30 space-y-1.5 text-xs">
            <MitreTag tactic={alert.mitre_attack.tactic} technique={alert.mitre_attack.technique} />
            <p className="text-slate-400 mt-1">{alert.mitre_attack.name}</p>
          </div>
        </div>
      )}

      {/* XAI Explanations */}
      {alert.xai_explanation.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-aegis-muted uppercase tracking-widest">Why Flagged</p>
          <ul className="space-y-1.5">
            {alert.xai_explanation.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400 bg-aegis-bg rounded p-2 border border-aegis-border">
                <span className="text-aegis-accent mt-0.5 shrink-0">›</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Status Controls */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-aegis-muted uppercase tracking-widest">Update Status</p>
        <div className="flex gap-2">
          {(['new', 'investigating', 'resolved'] as AlertStatus[]).map(s => (
            <button key={s} onClick={() => onUpdateStatus(s)}
              className={`flex-1 py-1.5 text-[10px] font-medium rounded capitalize transition-colors border ${
                alert.status === s ? 'bg-aegis-accent text-aegis-bg border-aegis-accent' : 'border-aegis-border text-aegis-muted hover:text-white hover:border-aegis-accent/40'
              }`}>{s}</button>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
