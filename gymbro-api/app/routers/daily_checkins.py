from datetime import date, datetime, UTC
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..deps import get_user_id
from ..models import DailyCheckIn

router = APIRouter(prefix="/daily-checkins", tags=["daily-checkins"])


class DailyCheckInUpsert(SQLModel):
    """Payload model for creating/updating a daily check-in."""
    weight: Optional[float] = None
    trained: bool = False
    steps: Optional[int] = None
    protein_met: bool = False
    notes: Optional[str] = None


@router.get("", response_model=List[DailyCheckIn])
def list_daily_checkins(
    from_date: Optional[date] = Query(default=None, alias="from"),
    to_date: Optional[date] = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    query = select(DailyCheckIn).where(DailyCheckIn.user_id == user_id)
    if from_date:
        query = query.where(DailyCheckIn.checkin_date >= from_date)
    if to_date:
        query = query.where(DailyCheckIn.checkin_date <= to_date)
    query = query.order_by(DailyCheckIn.checkin_date)
    return session.exec(query).all()


@router.get("/today", response_model=DailyCheckIn)
def get_today_checkin(
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    today = date.today()
    existing = session.exec(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id, DailyCheckIn.checkin_date == today
        )
    ).first()
    if existing:
        return existing
    now = datetime.now(UTC)
    return DailyCheckIn(
        user_id=user_id,
        checkin_date=today,
        weight=None,
        trained=False,
        steps=None,
        protein_met=False,
        notes=None,
        created_at=now,
        updated_at=now,
    )


@router.get("/{checkin_date}", response_model=DailyCheckIn)
def get_checkin_by_date(
    checkin_date: date,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    """
    Get a check-in for a specific date.
    
    If no check-in exists for the requested date, returns a non-persisted template
    object with default values (id=None). This allows clients to pre-populate forms
    with default values without requiring a separate endpoint for templates.
    """
    existing = session.exec(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id, DailyCheckIn.checkin_date == checkin_date
        )
    ).first()
    if existing:
        return existing
    # Return non-persisted template check-in with default values
    now = datetime.now(UTC)
    return DailyCheckIn(
        user_id=user_id,
        checkin_date=checkin_date,
        weight=None,
        trained=False,
        steps=None,
        protein_met=False,
        notes=None,
        created_at=now,
        updated_at=now,
    )


@router.put("/{checkin_date}", response_model=DailyCheckIn, status_code=status.HTTP_200_OK)
def upsert_daily_checkin(
    checkin_date: date,
    payload: DailyCheckInUpsert,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    existing = session.exec(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id, DailyCheckIn.checkin_date == checkin_date
        )
    ).first()

    now = datetime.now(UTC)

    if existing:
        existing.weight = payload.weight
        existing.trained = payload.trained
        existing.steps = payload.steps
        existing.protein_met = payload.protein_met
        existing.notes = payload.notes
        existing.updated_at = now
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    new_checkin = DailyCheckIn(
        user_id=user_id,
        checkin_date=checkin_date,
        weight=payload.weight,
        trained=payload.trained,
        steps=payload.steps,
        protein_met=payload.protein_met,
        notes=payload.notes,
        created_at=now,
        updated_at=now,
    )
    session.add(new_checkin)
    session.commit()
    session.refresh(new_checkin)
    return new_checkin
