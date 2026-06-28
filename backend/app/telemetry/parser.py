import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# ── Zeek conn.log field order (TSV) ─────────────────────────────────────────
ZEEK_CONN_FIELDS = [
    "ts", "uid", "id.orig_h", "id.orig_p", "id.resp_h", "id.resp_p",
    "proto", "service", "duration", "orig_bytes", "resp_bytes",
    "conn_state", "local_orig", "local_resp", "missed_bytes", "history",
    "orig_pkts", "orig_ip_bytes", "resp_pkts", "resp_ip_bytes", "tunnel_parents",
]


@dataclass
class FlowMeta:
    source_ip: str
    dest_ip: str
    dest_port: int


@dataclass
class NetworkFlowEvent:
    timestamp: datetime
    flow_id: str          # Zeek UID
    meta: FlowMeta
    proto: str
    service: Optional[str]
    duration: float
    orig_bytes: int
    resp_bytes: int
    conn_state: str
    history: Optional[str]
    orig_pkts: int
    resp_pkts: int
    log_hash: str = field(default="", init=False)

    def __post_init__(self):
        self.log_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """SHA-256 for forensic integrity — tampering invalidates the hash."""
        raw = (
            f"{self.flow_id}"
            f"{self.timestamp.isoformat()}"
            f"{self.meta.source_ip}"
            f"{self.proto}"
            f"{self.duration}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_mongo_doc(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "flow_id": self.flow_id,
            "meta": {
                "source_ip": self.meta.source_ip,
                "dest_ip": self.meta.dest_ip,
                "dest_port": self.meta.dest_port,
            },
            "proto": self.proto,
            "service": self.service,
            "duration": self.duration,
            "orig_bytes": self.orig_bytes,
            "resp_bytes": self.resp_bytes,
            "conn_state": self.conn_state,
            "history": self.history,
            "orig_pkts": self.orig_pkts,
            "resp_pkts": self.resp_pkts,
            "log_hash": self.log_hash,
        }

    def to_redis_record(self) -> dict:
        """Flat dict for Redis Streams XADD — all values must be strings."""
        return {
            "flow_id": self.flow_id,
            "source_ip": self.meta.source_ip,
            "dest_ip": self.meta.dest_ip,
            "dest_port": str(self.meta.dest_port),
            "proto": self.proto,
            "service": self.service or "",
            "duration": str(self.duration),
            "orig_bytes": str(self.orig_bytes),
            "resp_bytes": str(self.resp_bytes),
            "conn_state": self.conn_state,
            "orig_pkts": str(self.orig_pkts),
            "resp_pkts": str(self.resp_pkts),
            "log_hash": self.log_hash,
            "ts": self.timestamp.isoformat(),
        }


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _safe_str(value: str) -> Optional[str]:
    return None if value in ("-", "", "C") else value


def parse_conn_log_line(line: str) -> Optional[NetworkFlowEvent]:
    """
    Parse a single TSV line from Zeek conn.log.
    Returns None if the line is a comment, header, or malformed.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("\t")
    if len(parts) < 20:
        return None

    try:
        ts_epoch = float(parts[0])
        timestamp = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)

        return NetworkFlowEvent(
            timestamp=timestamp,
            flow_id=parts[1],
            meta=FlowMeta(
                source_ip=parts[2],
                dest_ip=parts[4],
                dest_port=_safe_int(parts[5]),
            ),
            proto=parts[6],
            service=_safe_str(parts[7]),
            duration=_safe_float(parts[8]),
            orig_bytes=_safe_int(parts[9]),
            resp_bytes=_safe_int(parts[10]),
            conn_state=parts[11],
            history=_safe_str(parts[15]),
            orig_pkts=_safe_int(parts[16]),
            resp_pkts=_safe_int(parts[18]),
        )
    except Exception:
        return None
