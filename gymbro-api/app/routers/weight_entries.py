from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..deps import get_user_id
from ..models import WeightEntry

router = APIRouter(prefix="/weight-entries", tags=["weight-entries"])


class WeightEntryCreate(SQLModel):
    """Request model for creating a weight entry."""
    for_date: date
    weight_kg: float
    note: Optional[str] = None


@router.get("", response_model=List[WeightEntry])
def list_weight_entries(
    from_date: Optional[date] = Query(default=None, alias="from"),
    to_date: Optional[date] = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    query = select(WeightEntry).where(WeightEntry.user_id == user_id)
    if from_date:
        query = query.where(WeightEntry.for_date >= from_date)
    if to_date:
        query = query.where(WeightEntry.for_date <= to_date)
    query = query.order_by(WeightEntry.for_date)
    return session.exec(query).all()


@router.post("", response_model=WeightEntry, status_code=status.HTTP_201_CREATED)
def create_weight_entry(
    payload: WeightEntryCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    entry = WeightEntry(
        user_id=user_id,
        for_date=payload.for_date,
        weight_kg=payload.weight_kg,
        note=payload.note,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=WeightEntry)
def update_weight_entry(
    entry_id: int,
    payload: WeightEntryCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    entry = session.exec(
        select(WeightEntry).where(
            WeightEntry.id == entry_id, WeightEntry.user_id == user_id
        )
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight entry not found.")
    entry.weight_kg = payload.weight_kg
    entry.for_date = payload.for_date
    entry.note = payload.note
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight_entry(
    entry_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    entry = session.exec(
        select(WeightEntry).where(
            WeightEntry.id == entry_id, WeightEntry.user_id == user_id
        )
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight entry not found.")
    session.delete(entry)
    session.commit()
