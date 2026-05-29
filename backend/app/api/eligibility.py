from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.eligibility import EligibilityPatch
from app.services import eligibility_service


router = APIRouter(prefix="/deals", tags=["eligibility"])


@router.post("/{deal_id}/eligibility/run")
def run_eligibility(
    deal_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    try:
        return eligibility_service.run_eligibility_flow(db, deal_id=deal_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{deal_id}/eligibility")
def get_eligibility(
    deal_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    eligibility, conditions = eligibility_service.get_eligibility(db, deal_id=deal_id)
    if eligibility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eligibility not computed")
    return {
        "eligibility": eligibility.model_dump(mode="json"),
        "conditions": conditions.model_dump(mode="json"),
    }


@router.patch("/{deal_id}/eligibility")
def patch_eligibility(
    deal_id: int,
    payload: EligibilityPatch,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    try:
        eligibility, conditions = eligibility_service.patch_eligibility(db, deal_id=deal_id, patch=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "eligibility": eligibility.model_dump(mode="json"),
        "conditions": conditions.model_dump(mode="json"),
    }


@router.post("/{deal_id}/eligibility/approve")
def approve_eligibility(
    deal_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    try:
        eligibility = eligibility_service.approve_eligibility(db, deal_id=deal_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"eligibility": eligibility.model_dump(mode="json")}
