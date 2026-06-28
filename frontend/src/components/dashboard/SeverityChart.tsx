import React from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import type { AlertSummaryItem } from '@/types'

const COLORS = ['#ff3b5c', '#f59e0b', '#00d4ff', '#10b981', '#8b5cf6', '#ec4899']

interface Props { data: AlertSummaryItem[] }

export default function SeverityChart({ data }: Props) {
  const chartData = data.map(d => ({ name: d._id || 'Unknown', value: d.count }))
  if (chartData.length === 0) return <div className="h-32 flex items-center justify-center text-aegis-muted text-xs">No data</div>
  return (
    <ResponsiveContainer width="100%" height={140}>
      <PieChart>
        <Pie data={chartData} cx="50%" cy="50%" innerRadius={35} outerRadius={60} paddingAngle={3} dataKey="value">
          {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 8, fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
