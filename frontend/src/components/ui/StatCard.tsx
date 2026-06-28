import React from 'react'
import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface Props { icon: LucideIcon; label: string; value: number; color: 'accent' | 'danger' | 'warn' | 'success' }

const colorMap = { accent: 'text-aegis-accent bg-aegis-accent/10 border-aegis-accent/20', danger: 'text-aegis-danger bg-aegis-danger/10 border-aegis-danger/20', warn: 'text-aegis-warn bg-aegis-warn/10 border-aegis-warn/20', success: 'text-aegis-success bg-aegis-success/10 border-aegis-success/20' }

export default function StatCard({ icon: Icon, label, value, color }: Props) {
  return (
    <motion.div whileHover={{ y: -2 }} className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-aegis-muted uppercase tracking-wider">{label}</span>
        <div className={clsx('p-2 rounded-lg border', colorMap[color])}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-3xl font-bold text-white tabular-nums">{value.toLocaleString()}</p>
    </motion.div>
  )
}
