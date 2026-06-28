import asyncio
import logging
import os
import uuid
from typing import Optional

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

logger = logging.getLogger("aegisnet.deception.docker")

HONEYPOT_NETWORK = "aegis-honeynet"
DECOY_LABEL      = "aegisnet.decoy"
CONTAINER_PREFIX = "aegis-decoy-"

# Subnet reserved for decoy containers (not routable to production)
HONEYNET_SUBNET  = os.getenv("HONEYNET_SUBNET", "172.30.0.0/24")


class DockerManager:
    """
    Manages decoy container lifecycle using the Docker SDK.
    Containers are placed on the isolated 'aegis-honeynet' bridge network.
    """

    def __init__(self):
        try:
            self._client = docker.from_env()
            logger.info("[docker_mgr] Docker daemon connection established.")
        except DockerException as exc:
            logger.error(f"[docker_mgr] Cannot connect to Docker daemon: {exc}")
            self._client = None

    def _get_or_create_network(self) -> str:
        """Ensure the isolated honeypot bridge network exists. Returns network ID."""
        try:
            net = self._client.networks.get(HONEYPOT_NETWORK)
            logger.debug(f"[docker_mgr] Using existing network '{HONEYPOT_NETWORK}'.")
            return net.id
        except NotFound:
            logger.info(f"[docker_mgr] Creating isolated network '{HONEYPOT_NETWORK}'...")
            net = self._client.networks.create(
                HONEYPOT_NETWORK,
                driver="bridge",
                internal=True,           # No external routing
                ipam=docker.types.IPAMConfig(
                    pool_configs=[
                        docker.types.IPAMPool(subnet=HONEYNET_SUBNET)
                    ]
                ),
                options={"com.docker.network.bridge.enable_ip_masquerade": "false"},
                labels={DECOY_LABEL: "true"},
            )
            return net.id

    def deploy_decoy(
        self,
        image: str,
        decoy_id: str,
        internal_port: int,
        env_vars: dict = None,
    ) -> Optional[dict]:
        """
        Deploy a decoy container on the isolated honeypot network.
        Returns {'container_id': str, 'container_ip': str} or None on failure.
        """
        if not self._client:
            logger.error("[docker_mgr] Docker client unavailable.")
            return None

        self._get_or_create_network()
        container_name = f"{CONTAINER_PREFIX}{decoy_id[:12]}"

        try:
            logger.info(f"[docker_mgr] Deploying decoy '{container_name}' from image '{image}'...")
            container: Container = self._client.containers.run(
                image=image,
                name=container_name,
                network=HONEYPOT_NETWORK,
                detach=True,
                remove=False,
                read_only=True,          # Read-only root filesystem
                # No privileged — enforce least privilege
                privileged=False,
                cap_drop=["ALL"],
                cap_add=["NET_BIND_SERVICE"],
                security_opt=["no-new-privileges:true"],
                labels={
                    DECOY_LABEL: "true",
                    "aegisnet.decoy_id": decoy_id,
                },
                environment=env_vars or {},
                tmpfs={"/tmp": "size=32m,mode=1777"},
            )

            container.reload()
            networks = container.attrs["NetworkSettings"]["Networks"]
            container_ip = networks.get(HONEYPOT_NETWORK, {}).get("IPAddress", "")

            logger.info(f"[docker_mgr] Decoy '{container_name}' running at {container_ip}:{internal_port}")
            return {
                "container_id": container.id,
                "container_ip": container_ip,
                "container_name": container_name,
            }

        except DockerException as exc:
            logger.error(f"[docker_mgr] Failed to deploy decoy: {exc}")
            return None

    def stop_decoy(self, container_id: str) -> bool:
        """Stop and remove a decoy container by ID."""
        if not self._client:
            return False
        try:
            container = self._client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
            logger.info(f"[docker_mgr] Decoy container '{container_id[:12]}' terminated and removed.")
            return True
        except NotFound:
            logger.warning(f"[docker_mgr] Container '{container_id[:12]}' not found — already removed.")
            return True
        except DockerException as exc:
            logger.error(f"[docker_mgr] Failed to stop container '{container_id[:12]}': {exc}")
            return False

    def list_active_decoys(self) -> list:
        """Return all running containers bearing the aegisnet.decoy label."""
        if not self._client:
            return []
        try:
            return self._client.containers.list(
                filters={"label": DECOY_LABEL, "status": "running"}
            )
        except DockerException:
            return []
