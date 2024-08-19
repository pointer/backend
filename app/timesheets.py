from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db import get_async_session, TimeSheet
from app.schemas import TimeSheetCreate, TimeSheetUpdate, TimeSheetRead
from app.users import current_active_user, User

router = APIRouter()


@router.post("/timesheet", response_model=TimeSheetRead)
async def create_timesheet(timesheet: TimeSheetCreate, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    db_timesheet = TimeSheet(**timesheet.model_dump(), user_id=user.id)
    db.add(db_timesheet)
    await db.commit()
    return TimeSheetRead.model_validate(db_timesheet)


@router.get("/timesheets/", response_model=List[TimeSheetRead])
async def read_timesheets(skip: int = 0, limit: int = 100, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    timesheets = await db.execute(select(TimeSheet).where(TimeSheet.user_id == user.id).offset(skip).limit(limit))
    return timesheets.scalars().all()


@router.get("/timesheets/{month}", response_model=List[TimeSheetRead])
async def read_timesheets_by_month(month: str, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    timesheets = await db.execute(select(TimeSheet).where(TimeSheet.user_id == user.id, TimeSheet.month == month))
    return timesheets.scalars().all()


@router.put("/timesheet/{timesheet_id}", response_model=TimeSheetRead)
async def update_timesheet(timesheet_id: int, timesheet: TimeSheetUpdate, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    db_timesheet = await db.execute(select(TimeSheet).where(TimeSheet.id == timesheet_id, TimeSheet.user_id == user.id))
    db_timesheet = db_timesheet.scalars().first()
    if db_timesheet is None:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    for key, value in timesheet.dict(exclude_unset=True).items():
        setattr(db_timesheet, key, value)
    await db.commit()
    await db.refresh(db_timesheet)
    return db_timesheet


@router.delete("/timesheet/{timesheet_id}", response_model=TimeSheetRead)
async def delete_timesheet(timesheet_id: int, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    db_timesheet = await db.execute(select(TimeSheet).where(TimeSheet.id == timesheet_id, TimeSheet.user_id == user.id))
    db_timesheet = db_timesheet.scalars().first()
    if db_timesheet is None:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    await db.delete(db_timesheet)
    await db.commit()
    return db_timesheet