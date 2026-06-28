import random
import time
from typing import List, Dict, Any
from app.simulator.traffic_generator import ZeekFlowGenerator, EXTERNAL_IPS, INTERNAL_IPS

class AttackProfiles:
    
    @staticmethod
    def generate_background_traffic(count: int = 10) -> List[Dict[str, Any]]:
        flows = []
        for _ in range(count):
            src = random.choice(INTERNAL_IPS)
            dst = random.choice(EXTERNAL_IPS) if random.random() > 0.3 else random.choice(INTERNAL_IPS)
            flows.append(ZeekFlowGenerator.generate_flow(
                source_ip=src, dest_ip=dst, dest_port=random.choice([80, 443, 53]),
                proto="tcp" if random.random() > 0.1 else "udp",
                duration=random.uniform(0.1, 5.0),
                orig_bytes=random.randint(100, 5000),
                resp_bytes=random.randint(100, 15000),
                conn_state="SF", is_malicious=False
            ))
        return flows

    @staticmethod
    def port_scan(attacker_ip: str, target_ip: str, num_ports: int = 50) -> List[Dict[str, Any]]:
        """Tactic: Discovery (Reconnaissance)"""
        flows = []
        for port in random.sample(range(1, 1024), num_ports):
            flows.append(ZeekFlowGenerator.generate_flow(
                source_ip=attacker_ip, dest_ip=target_ip, dest_port=port,
                duration=0.001, orig_bytes=0, resp_bytes=0, conn_state="S0", history="S", is_malicious=True
            ))
        return flows

    @staticmethod
    def ssh_brute_force(attacker_ip: str, target_ip: str, attempts: int = 20) -> List[Dict[str, Any]]:
        """Tactic: Credential Access"""
        flows = []
        for _ in range(attempts):
            flows.append(ZeekFlowGenerator.generate_flow(
                source_ip=attacker_ip, dest_ip=target_ip, dest_port=22, service="ssh",
                duration=random.uniform(0.5, 2.0), orig_bytes=random.randint(1500, 3000), 
                resp_bytes=random.randint(2000, 4000), conn_state="SF", history="ShAdDaF", is_malicious=True
            ))
        return flows

    @staticmethod
    def web_exploit(attacker_ip: str, target_ip: str) -> List[Dict[str, Any]]:
        """Tactic: Initial Access / Exploitation"""
        flows = []
        # Probing
        for _ in range(5):
            flows.append(ZeekFlowGenerator.generate_flow(
                source_ip=attacker_ip, dest_ip=target_ip, dest_port=80, service="http",
                duration=random.uniform(0.05, 0.2), orig_bytes=random.randint(200, 400),
                resp_bytes=random.randint(400, 600), conn_state="SF", is_malicious=True
            ))
        # Exploit Payload
        flows.append(ZeekFlowGenerator.generate_flow(
            source_ip=attacker_ip, dest_ip=target_ip, dest_port=80, service="http",
            duration=random.uniform(1.0, 3.0), orig_bytes=random.randint(5000, 15000),
            resp_bytes=random.randint(10000, 50000), conn_state="SF", history="ShAdDaF", is_malicious=True
        ))
        return flows

    @staticmethod
    def lateral_movement(attacker_ip: str, internal_target_ip: str) -> List[Dict[str, Any]]:
        """Tactic: Lateral Movement (SMB/RDP probing)"""
        flows = []
        for port in [445, 3389, 135]:
            flows.append(ZeekFlowGenerator.generate_flow(
                source_ip=attacker_ip, dest_ip=internal_target_ip, dest_port=port,
                duration=random.uniform(0.1, 0.5), orig_bytes=random.randint(500, 1000),
                resp_bytes=random.randint(100, 500), conn_state="S0" if random.random() > 0.5 else "SF",
                is_malicious=True
            ))
        return flows

    @staticmethod
    def honeypot_interaction(attacker_ip: str, honeypot_ip: str) -> List[Dict[str, Any]]:
        """Tactic: Execution (Malware Drop Simulation via Honeypot)"""
        flows = []
        # Shell access / payload download
        flows.append(ZeekFlowGenerator.generate_flow(
            source_ip=attacker_ip, dest_ip=honeypot_ip, dest_port=23, service="telnet",
            duration=random.uniform(5.0, 15.0), orig_bytes=random.randint(1000, 5000),
            resp_bytes=random.randint(5000, 20000), conn_state="SF", history="ShAdDaF", is_malicious=True
        ))
        return flows
