import { create } from 'zustand'
import type { CurrentUser } from '@/types'

interface AuthState {
  token: string | null
  user: CurrentUser | null
  setToken: (token: string) => void
  setUser: (user: CurrentUser) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('aegis_token'),
  user: null,
  setToken: (token) => {
    localStorage.setItem('aegis_token', token)
    set({ token })
  },
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem('aegis_token')
    set({ token: null, user: null })
  },
}))
