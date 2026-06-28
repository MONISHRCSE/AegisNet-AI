import React, { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, Shield, Activity, Zap, Eye } from 'lucide-react'
import { correlationApi } from '@/api/services'
import { useAlertStore } from '@/stores/alertStore'
import SeverityBadge from '@/components/ui/SeverityBadge'
import MitreTag from '@/components/ui/MitreTag'
import StatCard from '@/components/ui/StatCard'
import ThreatFeed from '@/components/dashboard/ThreatFeed'
import SeverityChart from '@/components/dashboard/SeverityChart'

export default function Dashboard() {
  const { data: recentIncidentsRes } = useQuery({ 
    queryKey: ['recentIncidents'], 
    queryFn: () => correlationApi.listIncidents({ limit: 100 }), 
    refetchInterval: 10_000 
  })
  const { liveAlerts } = useAlertStore()

  const incidents = recentIncidentsRes?.data?.data ?? []

  const stats = useMemo(() => {
    return {
      total:    incidents.length,
      critical: incidents.filter((i: any) => i.severity === 'CRITICAL' || i.severity === 'HIGH').length,
      active:   incidents.filter((i: any) => i.status === 'open' || i.status === 'investigating').length,
      attackers: [...new Set(incidents.map((i: any) => i.attacker_ip))].length,
    }
  }, [incidents])

  // Derive breakdown from incidents instead of raw alerts
  const breakdown = useMemo(() => {
    const counts: Record<string, number> = {}
    incidents.forEach((inc: any) => {
      if (inc.attack_chain && inc.attack_chain.length > 0) {
        const cat = inc.attack_chain[inc.attack_chain.length - 1]
        counts[cat] = (counts[cat] || 0) + 1
      } else {
        counts['Unknown'] = (counts['Unknown'] || 0) + 1
      }
    })
    return Object.entries(counts).map(([k, v]) => ({ _id: k, count: v })).sort((a, b) => b.count - a.count)
  }, [incidents])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Security Overview</h1>
          <p className="text-aegis-muted text-sm mt-0.5">Real-time threat intelligence dashboard</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-aegis-success bg-aegis-success/10 px-3 py-1.5 rounded-full border border-aegis-success/20">
          <span className="w-1.5 h-1.5 bg-aegis-success rounded-full animate-pulse" />
          MONITORING ACTIVE
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={AlertTriangle} label="Total Incidents" value={stats.total}    color="accent" />
        <StatCard icon={Zap}           label="Critical Threats" value={stats.critical}  color="danger" />
        <StatCard icon={Eye}           label="Active Incidents" value={stats.active}    color="warn" />
        <StatCard icon={Activity}      label="Unique Attackers" value={stats.attackers} color="success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Live Feed */}
        <div className="lg:col-span-2 glass-card p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 bg-aegis-danger rounded-full animate-ping" />
              Live Threat Feed (Raw Alerts)
            </h2>
            <span className="text-xs text-aegis-muted">{liveAlerts.length} events buffered</span>
          </div>
          <ThreatFeed alerts={liveAlerts} />
        </div>

        {/* Category Breakdown */}
        <div className="glass-card p-4">
          <h2 className="text-sm font-semibold text-white mb-4">Attack Categories</h2>
          <SeverityChart data={breakdown} />
          <div className="mt-4 space-y-2">
            {breakdown.slice(0, 5).map((item) => (
              <div key={item._id} className="flex items-center justify-between text-xs">
                <span className="text-aegis-muted">{item._id || 'Unknown'}</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 bg-aegis-border rounded-full h-1">
                    <div className="h-1 rounded-full bg-aegis-accent" style={{ width: `${Math.min((item.count / (stats.total || 1)) * 100, 100)}%` }} />
                  </div>
                  <span className="text-slate-300 w-6 text-right">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
