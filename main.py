from fastapi import FastAPI
from database import engine
import database_models
from auth import auth_router

from routers import (
    user_router,
    blood_router,
    sos_router,
    home_router,
    medicine_router,
    lost_found_router,
    hazard_router,
)

database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neighborly API",
    description="Community support platform — blood donors, SOS, home listings, medicine exchange, lost & found, hazard alerts",
    version="1.0.0",
)

app.include_router(user_router)
app.include_router(blood_router)
app.include_router(sos_router)
app.include_router(home_router)
app.include_router(medicine_router)
app.include_router(lost_found_router)
app.include_router(hazard_router)
app.include_router(auth_router)



@app.get("/")
def root():
    return {"message": "Neighborly API is running"}