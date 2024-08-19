import os
import ssl
from datetime import datetime, timedelta
from workalendar.europe import France
import calendar
from calendar import monthrange
from typing import Union, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, date
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi import HTTPException, Header
from fastapi_users.exceptions import UserAlreadyExists
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.router import ErrorCode
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import FastAPIUsers, password, schemas, BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
# from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
# from starlette.requests import Headers, Request
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from starlette.responses import Response

# from typing import
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db import User, create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users
import logging
from dotenv import load_dotenv
# from loguru import logger
from app.users import UserManager, get_user_manager
from app.timesheets import router as timesheet_router
from app.approbation import router as approbation_router
# from main import ssl_cert, ssl_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield

# ssl_cert = os.getenv("CERT_FILE", '../certs/example.com+5.pem')
# ssl_key = os.getenv("KEY_FILE", '../certs/example.com+5-key.pem')
# if not os.path.isfile(ssl_cert) or not os.path.isfile(ssl_key):
#     from os.path import dirname as up

#     dir = up(up(up(__file__)))

#     cert_file_path = os.path.join(dir, "certs")
#     ssl_cert = os.path.join(cert_file_path, "example.com+5.pem")
#     ssl_key = os.path.join(cert_file_path, "example.com+5-key.pem")
# app = FastAPI(ssl_keyfile=ssl_key, ssl_certfile=ssl_cert, lifespan=lifespan)
app = FastAPI(lifespan=lifespan)
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cra-5cc1c9a7f4d3.herokuapp.com/", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: str
    id: int
    is_active: bool
    role: bool
    working_days: int


class RegisterResponse(BaseModel):
    pass


def calculate_working_days():
    today = datetime.now()
    first_day = today.replace(day=1)
    last_day = (today.replace(day=1) + timedelta(days=32)
                ).replace(day=1) - timedelta(days=1)

    working_days = 0
    current_day = first_day
    while current_day <= last_day:
        if current_day.weekday() < 5:  # Monday to Friday
            working_days += 1
        current_day += timedelta(days=1)

    return working_days


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@app.middleware("https")
async def log_request(request: Request, call_next):
    # Log the request details
    # logger.info(f"Received request: {request.method} {request.url}")
    # logger.info(f"Headers: {dict(request.headers)}")

    # For POST requests, log the body
    if request.method == "POST":
        body = await request.body()
        logger.info(f"Body: {body.decode()}")
        # req_body = [section async for section in request.body.__dict__['body_iterator']]
        # logging.info("BODY:", req_body)
        # logger.info(
        #     f"{request.method} request to {request.url} metadata\n"
        #     f"\tHeaders: {request.headers}\n"
        #     f"\tBody: {request.body()}\n"
        #     f"\tPath Params: {request.path_params}\n"
        #     f"\tQuery Params: {request.query_params}\n"
        #     f"\tCookies: {request.cookies}\n"
        # )
    response = await call_next(request)
    return response


@app.post("/auth/register", response_model=UserRead)
async def register(
    user: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        # Convert datetime to date for SQLite
        if user.date_start:
            user.date_start = user.date_start.date()
        if user.date_end:
            user.date_end = user.date_end.date()
        created_user = await user_manager.create(user)
        logger.info(f"User {created_user.id} has registered.")
        return UserRead(
            id=created_user.id,
            email=created_user.email,
            is_active=created_user.is_active,
            is_superuser=created_user.is_superuser,
            is_verified=created_user.is_verified,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            phone=created_user.phone,
            role=created_user.role,
            contract_number=created_user.contract_number,
            company=created_user.company,
            company_id=created_user.company_id,
            tax_number=created_user.tax_number,
            client=created_user.client,
            project=created_user.project,
            city=created_user.city,
            date_start=created_user.date_start,
            date_end=created_user.date_end,
            rate=created_user.rate,
            approver=created_user.approver
        )
    except UserAlreadyExists:
        logger.error(f"Registration failed: User with email {user.email} already exists")
        raise HTTPException(
            status_code=400,
            detail="REGISTER_USER_ALREADY_EXISTS",
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration",
        )


@app.post("/auth/jwt/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        user = await user_manager.authenticate(credentials)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    access_token = await auth_backend.get_strategy().write_token(user)
    working_days = calculate_working_days()
    # print(">>>>>>>>>>>>> Working_days: ", working_days)
    respnse = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user.email,
        id=user.id,
        is_active=user.is_active,
        role=user.is_superuser,
        working_days=working_days
    )
    # print(">>>>>>>>>>>>>Login Response: ", respnse)
    return respnse

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
# app.include_router(timesheet_router, prefix="/api", tags=["timesheets"])
app.include_router(
    timesheet_router,
    prefix="/api",
    tags=["timesheets"],
    dependencies=[Depends(fastapi_users.current_user())]
)

app.include_router(
    approbation_router,
    prefix="/api",
    tags=["approbations"]
    # dependencies=[Depends(fastapi_users.current_user())]
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
