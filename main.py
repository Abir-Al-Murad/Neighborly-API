import os
import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from database import engine
import database_models
from routers.auth import auth_router

from routers import (
    user,
    blood,
    hazard_alert,
    home_listing,
    medicine_exchange,
    lost_and_found,
    sos,
)

database_models.Base.metadata.create_all(bind=engine)

BASE_URL = os.getenv("BASE_URL", "https://neighborly-api-f6i5.onrender.com")

servers = [{"url": BASE_URL}]

app = FastAPI(
    title="Neighborly API",
    description="Community support platform — blood donors, SOS, home listings, medicine exchange, lost & found, hazard alerts",
    version="1.0.0",
    servers=servers,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"isSuccess": False, "error": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"isSuccess": False, "error": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"isSuccess": False, "error": "Internal server error"},
    )


@app.middleware("http")
async def response_envelope_middleware(request: Request, call_next):
    if request.url.path in {"/openapi.json", "/docs", "/redoc"}:
        return await call_next(request)

    response = await call_next(request)

    safe_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-length", "content-type", "transfer-encoding"}
    }

    if response.status_code in {204, 304}:
        return Response(
            content=b"",
            status_code=response.status_code,
            headers=safe_headers,
            media_type=response.media_type,
        )

    content_type = response.headers.get("content-type", "")
    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    if "application/json" not in content_type.lower():
        return Response(
            content=body,
            status_code=response.status_code,
            headers=safe_headers,
            media_type=response.media_type,
        )

    try:
        payload = json.loads(body) if body else None
    except json.JSONDecodeError:
        return Response(
            content=body,
            status_code=response.status_code,
            headers=safe_headers,
            media_type=response.media_type,
        )

    if isinstance(payload, dict) and "isSuccess" in payload and ("data" in payload or "error" in payload):
        return JSONResponse(
            status_code=response.status_code,
            content=payload,
            headers=safe_headers,
        )

    return JSONResponse(
        status_code=response.status_code,
        content={"isSuccess": True, "data": payload},
        headers=safe_headers,
    )

# Enable CORS for the deployed base URL (and local dev if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",
        # "http://localhost:5000",
        # "http://localhost:8080",
        # "http://127.0.0.1:5500",
        # "http://localhost:63558",  # flutter web dynamic port
        # BASE_URL,
            "*"  # Allow all origins for testing; replace with specific URLs in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user.user_router)
app.include_router(blood.blood_router)
app.include_router(sos.sos_router)
app.include_router(home_listing.home_router)
app.include_router(medicine_exchange.medicine_router)
app.include_router(lost_and_found.lost_found_router)
app.include_router(hazard_alert.hazard_router)




@app.get("/")
def root():
    return {"message": "Neighborly API is running"}