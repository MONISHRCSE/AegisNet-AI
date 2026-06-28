import logging
from typing import Dict, List
from app.correlation.models import TopologyNode, TopologyEdge, TopologyGraph

logger = logging.getLogger("aegisnet.correlation.topology")

class TopologyService:
    def __init__(self):
        self.graph = TopologyGraph()
        self.nodes_by_id: Dict[str, TopologyNode] = {}
        self.edges_set = set()

    def add_node(self, node_id: str, type_: str, label: str, severity: str = "low"):
        if node_id not in self.nodes_by_id:
            node = TopologyNode(id=node_id, type=type_, label=label, severity=severity)
            self.nodes_by_id[node_id] = node
            self.graph.nodes.append(node)
        else:
            # Update severity if higher
            existing = self.nodes_by_id[node_id]
            levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            if levels.get(severity.lower(), 0) > levels.get(existing.severity.lower(), 0):
                existing.severity = severity

    def add_edge(self, source: str, target: str, type_: str):
        edge_id = f"{source}-{target}-{type_}"
        if edge_id not in self.edges_set:
            edge = TopologyEdge(source=source, target=target, type=type_)
            self.edges_set.add(edge_id)
            self.graph.edges.append(edge)

    def process_incident(self, incident):
        # Add attacker node
        self.add_node(incident.attacker_ip, type_="attacker", label="Threat Actor", severity=incident.severity.lower())
        
        # Add targets and edges
        for target_ip in incident.target_ips:
            # We don't know if target is honeypot or asset just from incident, assume asset unless specified
            self.add_node(target_ip, type_="asset", label=f"Asset {target_ip}")
            self.add_edge(source=incident.attacker_ip, target=target_ip, type_="malicious_flow")

    def get_live_graph(self) -> dict:
        return self.graph.to_dict()
