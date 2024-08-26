from datetime import datetime
from typing import AsyncGenerator
import asyncio
import os
# from asyncmy import connect
# from asyncmy.cursors import DictCursor
from icecream import ic
import aiomysql
from aiomysql import DictCursor
from dotenv import load_dotenv
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from fastapi import Depends

from dotenv import load_dotenv
# Load the .env file
load_dotenv(".env")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
# ic(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)

DB_URL = f'mysql+aiomysql://{DB_USER}:{DB_PASS}@{ DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
# DB_URL = f'mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4&auth_plugin=mysql_native_password'
# DB_URL = 'mysql+aiomysql://{}:{}@{}:{}/{}?charset=utf8mb4&collation=utf8mb4_general_ci'.format(
# DB_URL = 'mysql+aiomysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
#     DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
# ic(DB_URL)

class Base(DeclarativeBase):
    pass


# class User(SQLAlchemyBaseUserTableUUID, Base):
#     pass

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(2048), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), nullable=True)
    contract_number = Column(String(50), nullable=True)
    company = Column(String(100), nullable=True)
    company_id = Column(String(50), nullable=True)
    tax_number = Column(String(50), nullable=True)
    client = Column(String(100), nullable=True)
    project = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    zip = Column(String(20), nullable=True)
    date_start = Column(Date, nullable=True)
    date_end = Column(Date, nullable=True)
    rate = Column(Numeric, nullable=True)
    approver = Column(Integer,  nullable=True)


class TimeSheet(Base):
    __tablename__ = "timesheet"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_account.id"))
    date = Column(Date, nullable=False)
    worked_days = Column(Integer, nullable=False)
    working_days = Column(Integer, nullable=False)
    month = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    status = Column(String(20), default='pending')

    user = relationship("User", back_populates="timesheets")


User.timesheets = relationship("TimeSheet", back_populates="user")

engine = create_async_engine(DB_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Approbation(Base):
    __tablename__ = "approbation"

    id = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheet.id"))
    supervisor_id = Column(Integer, ForeignKey("user_account.id"))
    approved = Column(Boolean, nullable=False)
    approval_date = Column(DateTime, default=datetime.utcnow)

    timesheet = relationship("TimeSheet", back_populates="approbations")
    supervisor = relationship("User", back_populates="approbations")


TimeSheet.approbations = relationship(
    "Approbation", back_populates="timesheet")

User.approbations = relationship("Approbation", back_populates="supervisor")


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
