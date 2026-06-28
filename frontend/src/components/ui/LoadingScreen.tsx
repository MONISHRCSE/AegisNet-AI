import React from 'react'
import { Shield } from 'lucide-react'

export default function LoadingScreen() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-aegis-bg gap-4">
      <div className="relative">
        <Shield className="w-10 h-10 text-aegis-accent" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-aegis-accent rounded-full animate-ping" />
      </div>
      <p className="text-aegis-muted text-sm font-mono animate-pulse">INITIALISING AEGISNET...</p>
    </div>
  )
}
