from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    get_escalations,
    get_escalation,
    update_escalation,
    init_db,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="FinSaathi Human Support API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class EscalationUpdate(BaseModel):
    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
    ]

    resolution: str | None = None


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup() -> None:
    init_db()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "service": "FinSaathi Human Support API",
        "status": "running",
    }


@app.get("/api/health")
def health():
    return {
        "success": True,
        "status": "healthy",
    }


# ============================================================
# GET ALL ESCALATIONS
# ============================================================

@app.get("/api/escalations")
def list_escalations(
    status: str | None = None,
):
    """
    Return all human-support escalations.

    Optional:
        /api/escalations?status=OPEN
    """

    if status:
        status = status.upper().strip()

        allowed_statuses = {
            "OPEN",
            "IN_PROGRESS",
            "RESOLVED",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status.",
            )

    escalations = get_escalations(
        status=status
    )

    return {
        "success": True,
        "count": len(escalations),
        "escalations": escalations,
    }


# ============================================================
# GET ONE ESCALATION
# ============================================================

@app.get("/api/escalations/{request_id}")
def get_single_escalation(
    request_id: str,
):
    """
    Return one escalation using its reference ID.

    Example:
        /api/escalations/FS-A5323F
    """

    escalation = get_escalation(
        request_id
    )

    if escalation is None:
        raise HTTPException(
            status_code=404,
            detail="Escalation not found.",
        )

    return {
        "success": True,
        "escalation": escalation,
    }


# ============================================================
# UPDATE ESCALATION
# ============================================================

@app.patch(
    "/api/escalations/{request_id}"
)
def change_escalation_status(
    request_id: str,
    payload: EscalationUpdate,
):
    """
    Update human-support request status.

    OPEN
        ↓
    IN_PROGRESS
        ↓
    RESOLVED
    """

    existing = get_escalation(
        request_id
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Escalation not found.",
        )

    # Resolution should be supplied when
    # marking a request as resolved.
    if (
        payload.status == "RESOLVED"
        and not payload.resolution
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Resolution is required "
                "when marking an escalation "
                "as RESOLVED."
            ),
        )

    updated = update_escalation(
        request_id=request_id,
        status=payload.status,
        resolution=payload.resolution,
    )

    if not updated:
        raise HTTPException(
            status_code=500,
            detail="Could not update escalation.",
        )

    updated_escalation = get_escalation(
        request_id
    )

    return {
        "success": True,
        "message": "Escalation updated successfully.",
        "escalation": updated_escalation,
    }
