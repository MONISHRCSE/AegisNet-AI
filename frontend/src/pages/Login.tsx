import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/services'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd,  setShowPwd]  = useState(false)
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const { setToken, setUser } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data: tokenData } = await authApi.login({ username, password })
      setToken(tokenData.access_token)
      const { data: me } = await authApi.me()
      setUser(me)
      navigate('/')
    } catch {
      setError('Invalid credentials. Check your username and password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-aegis-bg overflow-hidden relative">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-30" />
      <div className="absolute inset-0 bg-gradient-radial from-aegis-accent/5 via-transparent to-transparent" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="glass-card p-8 accent-glow">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div className="relative mb-4">
              <div className="w-16 h-16 rounded-2xl bg-aegis-accent/10 border border-aegis-accent/30 flex items-center justify-center">
                <Shield className="w-8 h-8 text-aegis-accent" />
              </div>
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-aegis-accent rounded-full animate-ping" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-wider">AEGISNET AI</h1>
            <p className="text-aegis-muted text-xs mt-1 tracking-widest">CYBER DEFENSE PLATFORM</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-aegis-muted mb-1.5">USERNAME</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-aegis-bg border border-aegis-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-aegis-muted/50 focus:outline-none focus:border-aegis-accent/60 focus:ring-1 focus:ring-aegis-accent/30 transition-all"
                placeholder="analyst@aegisnet"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-aegis-muted mb-1.5">PASSWORD</label>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-aegis-bg border border-aegis-border rounded-lg px-4 py-2.5 pr-10 text-sm text-white placeholder-aegis-muted/50 focus:outline-none focus:border-aegis-accent/60 focus:ring-1 focus:ring-aegis-accent/30 transition-all"
                  placeholder="••••••••"
                  required
                />
                <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-2.5 text-aegis-muted hover:text-slate-300">
                  {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-aegis-danger text-xs bg-aegis-danger/10 border border-aegis-danger/20 rounded-lg px-3 py-2">
                {error}
              </motion.p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
              {loading ? 'Authenticating...' : 'Access Command Center'}
            </button>
          </form>

          <p className="text-center text-aegis-muted/60 text-xs mt-6 font-mono">
            AEGISNET AI v1.0 · CLASSIFIED
          </p>
        </div>
      </motion.div>
    </div>
  )
}
