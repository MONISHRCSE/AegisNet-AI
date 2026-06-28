// ── Auth ────────────────────────────────────────────────────────────────────
export interface LoginCredentials { username: string; password: string }
export interface AuthToken { access_token: string; token_type: string }
export interface CurrentUser { username: string; role: 'Admin' | 'Analyst' | 'Viewer' }

// ── Network Flows ────────────────────────────────────────────────────────────
export interface NetworkFlow {
  flow_id: string
  timestamp: string
  meta: { source_ip: string; dest_ip: string; dest_port: number }
  proto: string
  service?: string
  duration: number
  orig_bytes: number
  resp_bytes: number
  conn_state: string
  orig_pkts: number
  resp_pkts: number
  log_hash: string
}

// ── ML Classification ────────────────────────────────────────────────────────
export interface MLClassification {
  model: string
  category: string
  confidence: number
}

export interface MitreAttack {
  tactic: string
  technique: string
  name: string
}

export type AlertStatus = 'new' | 'investigating' | 'resolved'
export type Severity    = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface SecurityAlert {
  _id: string
  _alert_id: string
  timestamp: string
  flow_id: string
  attacker_ip: string
  target_ip: string
  ml_classification: MLClassification
  anomaly_score: number
  severity_score: number
  mitre_attack?: MitreAttack
  xai_explanation: string[]
  status: AlertStatus
}

// ── Honeypot ─────────────────────────────────────────────────────────────────
export interface HoneypotInteraction {
  _id: string
  timestamp: string
  decoy_id: string
  attacker_ip: string
  honeypot_type: string
  interaction_type: string
  payload: Record<string, unknown>
  session_id: string
  log_hash: string
}

export interface ActiveDecoy {
  id: string
  assigned_ip: string
  target_attacker_ip: string
  status: 'pending' | 'running' | 'stopped' | 'archived'
  template_id: number
  terminated_at?: string
  created_at: string
  updated_at: string
  template?: HoneypotTemplate
}

export interface HoneypotTemplate {
  id: number
  name: string
  docker_image: string
  target_ports: number[]
  interaction_level: 'low' | 'medium' | 'high'
  env_vars: Record<string, string>
}

// ── Assets ───────────────────────────────────────────────────────────────────
export interface Asset {
  id: string
  ip_address: string
  mac_address?: string
  hostname?: string
  os_fingerprint?: string
  criticality_score: number
  is_honeypot: boolean
  last_seen?: string
}

// ── Threat Intelligence ──────────────────────────────────────────────────────
export interface ThreatIntelligence {
  id: string
  indicator: string
  indicator_type: 'ip' | 'domain' | 'hash'
  source: string
  confidence_score: number
  tags: string[]
}

// ── WebSocket Events ─────────────────────────────────────────────────────────
export type WsEventType = 'alert' | 'flow' | 'honeypot_interaction' | 'decoy_event'
export interface WsMessage<T = unknown> {
  type: WsEventType
  data: T
}

// ── Dashboard Summary ────────────────────────────────────────────────────────
export interface AlertSummaryItem {
  _id: string
  count: number
  avg_severity: number
  max_severity: number
}
export interface AlertSummary { breakdown: AlertSummaryItem[] }
