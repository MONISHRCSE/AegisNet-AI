import asyncio
import logging
import subprocess
from typing import Optional

logger = logging.getLogger("aegisnet.deception.iptables")


class IPTablesManager:
    """
    Manages iptables DNAT rules to transparently redirect attacker traffic
    from the real network to isolated decoy containers on aegis-honeynet.

    IMPORTANT: Requires NET_ADMIN capability or root on the host.
    In production, this should be executed via a privileged sidecar container
    or a controlled privileged service boundary.

    Rules added follow the form:
      iptables -t nat -A PREROUTING
        -s <attacker_ip>
        -p tcp --dport <target_port>
        -j DNAT --to-destination <decoy_ip>:<decoy_port>
    """

    async def _run(self, args: list[str]) -> bool:
        """Execute an iptables command as a subprocess."""
        cmd = ["iptables"] + args
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error(f"[iptables] Command failed: {' '.join(cmd)}\n{stderr.decode()}")
                return False
            logger.debug(f"[iptables] OK: {' '.join(cmd)}")
            return True
        except FileNotFoundError:
            logger.warning("[iptables] iptables binary not found — skipping NAT rule (dev mode).")
            return False
        except Exception as exc:
            logger.error(f"[iptables] Unexpected error: {exc}")
            return False

    async def add_dnat_rule(
        self,
        attacker_ip: str,
        target_port: int,
        decoy_ip: str,
        decoy_port: int,
        protocol: str = "tcp",
    ) -> bool:
        """
        Redirect traffic from attacker_ip:target_port to decoy_ip:decoy_port.
        """
        logger.info(
            f"[iptables] Adding DNAT: {attacker_ip}:{target_port} "
            f"→ {decoy_ip}:{decoy_port}"
        )
        return await self._run([
            "-t", "nat", "-A", "PREROUTING",
            "-s", attacker_ip,
            "-p", protocol,
            "--dport", str(target_port),
            "-j", "DNAT",
            "--to-destination", f"{decoy_ip}:{decoy_port}",
        ])

    async def remove_dnat_rule(
        self,
        attacker_ip: str,
        target_port: int,
        decoy_ip: str,
        decoy_port: int,
        protocol: str = "tcp",
    ) -> bool:
        """Remove a previously installed DNAT rule."""
        logger.info(
            f"[iptables] Removing DNAT: {attacker_ip}:{target_port} "
            f"→ {decoy_ip}:{decoy_port}"
        )
        return await self._run([
            "-t", "nat", "-D", "PREROUTING",
            "-s", attacker_ip,
            "-p", protocol,
            "--dport", str(target_port),
            "-j", "DNAT",
            "--to-destination", f"{decoy_ip}:{decoy_port}",
        ])

    async def block_attacker_ip(self, attacker_ip: str) -> bool:
        """Drop all forwarded packets from a confirmed attacker IP."""
        logger.info(f"[iptables] Blocking attacker IP: {attacker_ip}")
        return await self._run([
            "-A", "FORWARD",
            "-s", attacker_ip,
            "-j", "DROP",
        ])

    async def unblock_attacker_ip(self, attacker_ip: str) -> bool:
        return await self._run([
            "-D", "FORWARD",
            "-s", attacker_ip,
            "-j", "DROP",
        ])
