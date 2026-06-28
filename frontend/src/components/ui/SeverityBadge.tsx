import React from 'react'
import clsx from 'clsx'

interface Props { score: number }

export default function SeverityBadge({ score }: Props) {
  const { label, cls } = score >= 8
    ? { label: 'CRITICAL', cls: 'severity-critical' }
    : score >= 6
    ? { label: 'HIGH',     cls: 'severity-high' }
    : score >= 3
    ? { label: 'MEDIUM',   cls: 'severity-medium' }
    : { label: 'LOW',      cls: 'severity-low' }

  return (
    <span className={clsx('text-[10px] font-mono font-bold px-2 py-0.5 rounded border', cls)}>
      {label} {score.toFixed(1)}
    </span>
  )
}
