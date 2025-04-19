import logging
import logging.config
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from swiftatlas.routers.swift_codes import router as swift_router

from swiftatlas import settings
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


logging.config.fileConfig("swiftatlas/logger_conf.ini", disable_existing_loggers=False)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb = app.mongodb_client[settings.MONGODB_DB_NAME]
    logger.info(f"Connected to MongoDB: {app.mongodb}")

    yield

    app.mongodb_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(swift_router)


# @app.exception_handler(RequestValidationError)
# async def custom_validation_exception_handler(
#     request: Request, exc: RequestValidationError
# ):
#     error_messages = []
#     for error in exc.errors():
#         loc = " -> ".join(str(l) for l in error["loc"])
#         msg = error["msg"]
#         error_messages.append(f"{loc}: {msg}")

#     message = "Validation failed: " + "; ".join(error_messages)

#     return JSONResponse(
#         status_code=HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"message": message},
#     )
