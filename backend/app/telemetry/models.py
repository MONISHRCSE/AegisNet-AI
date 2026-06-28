from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NetworkFlowEvent(BaseModel):
    ts: datetime

    source_ip: str
    source_port: int

    destination_ip: str
    destination_port: int

    protocol: str

    service: Optional[str] = None

    duration: float = 0.0

    bytes_sent: int = 0
    bytes_received: int = 0

    connection_state: Optional[str] = None

    local_orig: Optional[bool] = None
    local_resp: Optional[bool] = None

    missed_bytes: int = 0

    history: Optional[str] = None

    packets_sent: int = 0
    packets_received: int = 0

    flow_hash: Optional[str] = None