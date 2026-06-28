import React from 'react'

interface Props { tactic: string; technique: string }

export default function MitreTag({ tactic, technique }: Props) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-[9px] font-mono px-1.5 py-0.5 bg-purple-900/40 text-purple-300 border border-purple-700/30 rounded">
        {tactic}
      </span>
      <span className="text-[9px] font-mono px-1.5 py-0.5 bg-indigo-900/40 text-indigo-300 border border-indigo-700/30 rounded">
        {technique}
      </span>
    </div>
  )
}
