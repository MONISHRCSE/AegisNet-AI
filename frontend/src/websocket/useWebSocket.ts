import { useCallback, useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { WsMessage } from '@/types'
import { useAlertStore } from '@/stores/alertStore'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/telemetry`
const RECONNECT_DELAY_MS = 3000
const HEARTBEAT_INTERVAL = 25000

export function useWebSocket() {
  const wsRef        = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>()
  const heartbeatRef = useRef<ReturnType<typeof setInterval>>()
  const { addAlert } = useAlertStore()
  const queryClient  = useQueryClient()

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[ws] Connected to AegisNet telemetry stream.')
        heartbeatRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, HEARTBEAT_INTERVAL)
      }

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: WsMessage = JSON.parse(event.data)
          if (msg.type === 'alert') {
            addAlert(msg.data as any)
          } else if (msg.type === 'INCIDENT_UPDATE') {
            queryClient.invalidateQueries({ queryKey: ['incidents'] })
            queryClient.invalidateQueries({ queryKey: ['recentIncidents'] })
          } else if (msg.type === 'TOPOLOGY_UPDATE') {
            queryClient.invalidateQueries({ queryKey: ['topologyLive'] })
          }
        } catch {
          // Non-JSON pong/keepalive responses — ignore
        }
      }

      ws.onclose = () => {
        console.warn('[ws] Disconnected — reconnecting in 3s...')
        clearInterval(heartbeatRef.current)
        reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }

      ws.onerror = (err) => {
        console.error('[ws] Error:', err)
        ws.close()
      }
    } catch (err) {
      console.error('[ws] Failed to connect:', err)
      reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }
  }, [addAlert])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectRef.current)
      clearInterval(heartbeatRef.current)
      wsRef.current?.close()
    }
  }, [connect])
}
