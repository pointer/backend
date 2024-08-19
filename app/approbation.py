from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db import get_async_session, Approbation, TimeSheet
from app.schemas import ApprobationCreate, ApprobationUpdate, ApprobationRead, TimeSheetRead
from app.users import current_active_user, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/approbation", response_model=ApprobationRead)
async def create_approbation(approbation: ApprobationCreate, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    approbation_data = approbation.model_dump()
    approbation_data['supervisor_id'] = user.id
    
    # Ensure timesheet_id is an integer
    timesheet_id = int(approbation_data['timesheet_id'])
    approbation_data['timesheet_id'] = timesheet_id

    db_approbation = Approbation(**approbation_data)
    db.add(db_approbation)
    await db.commit()
    await db.refresh(db_approbation)

    # Update the timesheet status
    result = await db.execute(select(TimeSheet).where(TimeSheet.id == timesheet_id))
    timesheet = result.scalar_one_or_none()
    if timesheet:
        timesheet.status = 'approved' if approbation.approved else 'rejected'
        await db.commit()

    return db_approbation


@router.get("/approbations/", response_model=List[ApprobationRead])
async def read_approbations(skip: int = 0, limit: int = 100, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(timesheet).offset(skip).limit(limit))
    approbations = result.scalars().all()
    return approbations


@router.get("/approbations/{month}/{approver}", response_model=List[TimeSheetRead])
async def read_approbation(month: str, approver: int, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(TimeSheet, User.first_name, User.last_name)
        .join(User, TimeSheet.user_id == User.id)
        .where(TimeSheet.month == month, TimeSheet.status == 'pending', User.approver == approver)
        .order_by(TimeSheet.id)
    )
    timesheets = result.all()
    if not timesheets:
        raise HTTPException(status_code=404, detail="Timesheets not found")

    timesheet_list = [
        {**timesheet.__dict__, 'first_name': first_name, 'last_name': last_name}
        for timesheet, first_name, last_name in timesheets
    ]

    return timesheet_list


@router.get("/approbations/{approbation_id}", response_model=ApprobationRead)
async def read_approbation(approbation_id: int, user: User = Depends(current_active_user), db: Session = Depends(get_async_session)):
    approbation = await db.query(Approbation).filter(Approbation.id == approbation_id).first()
    if approbation is None:
        raise HTTPException(status_code=404, detail="Approbation not found")
    return approbation


@router.put("/approbation/{approbation_id}", response_model=ApprobationRead)
async def update_approbation(approbation_id: int, approbation: ApprobationUpdate, user: User = Depends(current_active_user), db: Session = Depends(get_async_session)):
    db_approbation = await db.query(Approbation).filter(Approbation.id == approbation_id).first()
    if db_approbation is None:
        raise HTTPException(status_code=404, detail="Approbation not found")

    for key, value in approbation.model_dump().items():
        setattr(db_approbation, key, value)

    await db.commit()
    await db.refresh(db_approbation)

    # Update the timesheet status
    timesheet = await db.query(TimeSheet).filter(TimeSheet.id == db_approbation.timesheet_id).first()
    if timesheet:
        timesheet.status = 'approved' if db_approbation.approved else 'rejected'
        await db.commit()

    return db_approbation