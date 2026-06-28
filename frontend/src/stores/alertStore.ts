import { create } from 'zustand'
import type { SecurityAlert } from '@/types'

const MAX_LIVE_ALERTS = 200

interface AlertState {
  liveAlerts: SecurityAlert[]
  unreadCount: number
  addAlert: (alert: SecurityAlert) => void
  clearUnread: () => void
}

export const useAlertStore = create<AlertState>((set) => ({
  liveAlerts: [],
  unreadCount: 0,
  addAlert: (alert) =>
    set((state) => ({
      liveAlerts: [alert, ...state.liveAlerts].slice(0, MAX_LIVE_ALERTS),
      unreadCount: state.unreadCount + 1,
    })),
  clearUnread: () => set({ unreadCount: 0 }),
}))
