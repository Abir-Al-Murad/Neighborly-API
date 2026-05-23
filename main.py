import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import database_models
from routerss.auth import auth_router

from routerss import (
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
app.include_router(user.user_router)
app.include_router(blood.blood_router)
app.include_router(sos.sos_router)
app.include_router(home_listing.home_router)
app.include_router(medicine_exchange.medicine_router)
app.include_router(lost_and_found.lost_found_router)
app.include_router(hazard_alert.hazard_router)
app.include_router(auth_router)



@app.get("/")
def root():
    return {"message": "Neighborly API is running"}