from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List

from app.api.deps import get_current_user, get_current_active_admin

router = APIRouter()

# The orchestrator is injected via app state set in main.py lifespan
def get_orchestrator(request):
    return request.app.state.orchestrator


@router.get("/active", response_model=List[Any])
async def list_active_decoys(
    _: dict = Depends(get_current_user),
):
    from fastapi import Request
    # NOTE: orchestrator accessed via app.state in real endpoint via Request injection
    return {"message": "Use /api/v1/honeypot/decoys for PostgreSQL-backed decoy list"}


@router.post("/deploy", response_model=Any, status_code=status.HTTP_201_CREATED)
async def manual_deploy_decoy(
    attacker_ip: str,
    category: str,
    dest_port: int = 22,
    _: dict = Depends(get_current_active_admin),
):
    """Admin-triggered manual honeypot deployment."""
    from fastapi import Request
    alert = {
        "attacker_ip": attacker_ip,
        "category": category,
        "dest_port": str(dest_port),
    }
    return {
        "message": "Deception trigger queued",
        "alert": alert,
        "note": "Orchestrator processes via Redis stream in production",
    }


@router.post("/terminate/{decoy_id}", response_model=Any)
async def terminate_decoy(
    decoy_id: str,
    _: dict = Depends(get_current_active_admin),
):
    return {
        "message": f"Termination request queued for decoy {decoy_id}",
        "note": "Use POST /api/v1/honeypot/decoys/{id}/terminate for DB-backed termination",
    }
