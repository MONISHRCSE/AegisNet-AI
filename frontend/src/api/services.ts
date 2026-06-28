import api from './client'
import type {
  LoginCredentials, AuthToken, CurrentUser,
  SecurityAlert, AlertStatus, AlertSummary,
  NetworkFlow, HoneypotInteraction,
  ActiveDecoy, HoneypotTemplate,
  Asset, ThreatIntelligence,
} from '@/types'

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (creds: LoginCredentials) =>
    api.post<AuthToken>('/auth/login', new URLSearchParams({
      username: creds.username,
      password: creds.password,
    }), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }),
  me: () => api.get<CurrentUser>('/auth/me'),
}

// ── Alerts ───────────────────────────────────────────────────────────────────
// Removed alertsApi as the application now relies entirely on the Correlation Engine (incidents)

// ── Telemetry (MongoDB) ───────────────────────────────────────────────────────
export const telemetryApi = {
  flows: (params?: { source_ip?: string; limit?: number }) =>
    api.get<NetworkFlow[]>('/telemetry/flows', { params }),
  honeypotLogs: (params?: { attacker_ip?: string; limit?: number }) =>
    api.get<HoneypotInteraction[]>('/telemetry/honeypot-logs', { params }),
}

// ── Honeypot ─────────────────────────────────────────────────────────────────
export const honeypotApi = {
  templates: () => api.get<HoneypotTemplate[]>('/honeypot/templates'),
  decoys:    () => api.get<ActiveDecoy[]>('/honeypot/decoys'),
  terminate: (id: string) => api.post<ActiveDecoy>(`/honeypot/decoys/${id}/terminate`),
}

// ── Assets ───────────────────────────────────────────────────────────────────
export const assetsApi = {
  list: () => api.get<Asset[]>('/assets/'),
}

// ── Threat Intelligence ───────────────────────────────────────────────────────
export const threatIntelApi = {
  list:   (params?: { skip?: number; limit?: number }) => api.get<ThreatIntelligence[]>('/threat-intel/', { params }),
  delete: (indicator: string) => api.delete(`/threat-intel/${indicator}`),
}

// ── Correlation & Graph Intelligence ─────────────────────────────────────────
export const correlationApi = {
  listIncidents: (params?: { skip?: number; limit?: number }) => api.get('/correlation/incidents', { params }),
  getIncident: (id: string) => api.get(`/correlation/incidents/${id}`),
  getIncidentTimeline: (id: string) => api.get(`/correlation/incidents/${id}/timeline`),
  updateIncidentStatus: (id: string, status: string) => api.patch(`/correlation/incidents/${id}/status`, { status }),
  getTopology: () => api.get('/correlation/topology'),
  getTopologyLive: () => api.get('/correlation/topology/live'),
  getActiveDecoys: () => api.get('/correlation/decoys/active'),
  getForensicsReplay: (id: string) => api.get(`/correlation/forensics/replay/${id}`),
}
