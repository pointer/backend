from datetime import datetime
import uuid

from fastapi_users import schemas

from fastapi_users import schemas
from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class UserRead(schemas.BaseUser[int]):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str | None = None
    contract_number: str | None = None
    company: str | None = None
    company_id: str | None = None
    tax_number: str | None = None
    client: str | None = None
    project: str | None = None
    city: str | None = None
    zip: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    rate: Decimal | None = None
    approver: Decimal | None = None


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    phone: str | None = None
    role: str | None = None
    contract_number: str | None = None
    company: str | None = None
    company_id: str | None = None
    tax_number: str | None = None
    client: str | None = None
    project: str | None = None
    city: str | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None
    rate: float | None = None
    approver: Decimal | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.date().isoformat() if v else None
        }


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str | None = None
    contract_number: str | None = None
    company: str | None = None
    company_id: str | None = None
    tax_number: str | None = None
    client: str | None = None
    project: str | None = None
    city: str | None = None
    zip: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    rate: Decimal | None = None
    approver: Decimal | None = None


class TimeSheetBase(BaseModel):
    date: date
    worked_days: int
    working_days: int
    month: str


class TimeSheetCreate(TimeSheetBase):
    pass


class TimeSheetUpdate(TimeSheetBase):
    pass


class TimeSheetRead(TimeSheetBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    first_name: str | None = None
    last_name: str | None = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ApprobationBase(BaseModel):
    timesheet_id: int
    supervisor_id: int
    approved: bool


class ApprobationCreate(ApprobationBase):
    pass


class ApprobationUpdate(ApprobationBase):
    pass


class ApprobationRead(ApprobationBase):
    id: int
    approval_date: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
