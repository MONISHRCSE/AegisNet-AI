from typing import Optional, List
from dataclasses import dataclass, field


# ── Decoy type identifiers ──────────────────────────────────────────────────
class DecoyType:
    SSH     = "ssh-cowrie"
    MYSQL   = "mysql-fake"
    HTTP    = "http-admin-fake"
    FTP     = "ftp-fake"
    TCP     = "tcp-banner"


# ── Policy rule: maps ML alert category + optional port → decoy type ────────
@dataclass
class DeceptionRule:
    category: str                          # ML alert category (e.g. "BruteForce")
    dest_ports: List[int]                  # Ports that trigger this rule (empty = any)
    decoy_type: str                        # DecoyType constant
    priority: int = 5                      # Higher = evaluated first
    max_concurrent: int = 3               # Max simultaneous decoys of this type
    auto_terminate_minutes: int = 60      # Lifetime of the decoy


DECEPTION_POLICY: List[DeceptionRule] = [
    DeceptionRule(
        category="BruteForce",
        dest_ports=[22, 2222],
        decoy_type=DecoyType.SSH,
        priority=10,
        auto_terminate_minutes=120,
    ),
    DeceptionRule(
        category="Reconnaissance",
        dest_ports=[3306],
        decoy_type=DecoyType.MYSQL,
        priority=9,
    ),
    DeceptionRule(
        category="Reconnaissance",
        dest_ports=[80, 443, 8080, 8443],
        decoy_type=DecoyType.HTTP,
        priority=8,
    ),
    DeceptionRule(
        category="Reconnaissance",
        dest_ports=[21],
        decoy_type=DecoyType.FTP,
        priority=7,
    ),
    DeceptionRule(
        category="Reconnaissance",
        dest_ports=[],                     # Any port — catch-all
        decoy_type=DecoyType.TCP,
        priority=1,
        auto_terminate_minutes=30,
    ),
    DeceptionRule(
        category="WebAttack",
        dest_ports=[80, 443, 8080],
        decoy_type=DecoyType.HTTP,
        priority=9,
    ),
    DeceptionRule(
        category="DoS",
        dest_ports=[],
        decoy_type=DecoyType.TCP,
        priority=2,
        auto_terminate_minutes=20,
    ),
]


# ── Decoy Docker image mapping ───────────────────────────────────────────────
DECOY_IMAGE_MAP = {
    DecoyType.SSH:   "cowrie/cowrie:latest",
    DecoyType.MYSQL: "aegisnet/fake-mysql:latest",
    DecoyType.HTTP:  "aegisnet/fake-http-admin:latest",
    DecoyType.FTP:   "aegisnet/fake-ftp:latest",
    DecoyType.TCP:   "aegisnet/tcp-banner:latest",
}

# Ports exposed by each decoy container internally
DECOY_INTERNAL_PORT_MAP = {
    DecoyType.SSH:   2222,
    DecoyType.MYSQL: 3306,
    DecoyType.HTTP:  8080,
    DecoyType.FTP:   21,
    DecoyType.TCP:   9999,
}


def select_rule(category: str, dest_port: int) -> Optional[DeceptionRule]:
    """
    Select the highest-priority matching policy rule for a given
    alert category and destination port.
    Returns None if no rule matches.
    """
    candidates = []
    for rule in DECEPTION_POLICY:
        if rule.category != category:
            continue
        if rule.dest_ports and dest_port not in rule.dest_ports:
            continue
        candidates.append(rule)

    if not candidates:
        return None
    return max(candidates, key=lambda r: r.priority)
