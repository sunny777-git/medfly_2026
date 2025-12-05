import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models.database import Base, engine
from app.routers import (
    devices,
    hospitals,
    patient_registration,
    recordings,
    turnservers,
    users,
    departments,
    roles,
    procedures,
    snapshots,
    dashboard,        
)

import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="Medfly Hospital API")

# Ensure uploads folder exists
os.makedirs("uploads", exist_ok=True)

# Mount static and uploads
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

templates = Jinja2Templates(directory="app/templates")


# Serve /video HTML page
@app.get("/video", response_class=HTMLResponse)
async def video_page(request: Request, room: str | None = None):
    # If you are running Socket.IO separately, point to that URL
    signaling_url = os.getenv("SIGNALING_URL", "ws://localhost:9000")

    return templates.TemplateResponse(
        "video.html",
        {
            "request": request,
            "signaling_url": signaling_url,
            "room": room or "",
        },
    )


# Optional: Redirect /?room=xyz → /video?room=xyz
@app.get("/redirect-to-video")
async def redirect_to_video(room: str):
    return RedirectResponse(f"/video?room={room}")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="JWT Auth + FastAPI",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["Hospitals"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(roles.router, prefix="/api", tags=["Roles"])
app.include_router(procedures.router, prefix="/api", tags=["Procedures"])
app.include_router(patient_registration.router, prefix="/api", tags=["Patients"])
app.include_router(turnservers.router, prefix="/api", tags=["IceServers"])
app.include_router(snapshots.router, prefix="/api", tags=["Snapshots"])
app.include_router(recordings.router, prefix="/api", tags=["Recordings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"]) 


@app.get("/")
def root():
    return {"message": "Medfly iHome Page"}


@app.get("/watch", response_class=HTMLResponse)
async def watch_page(request: Request):
    return templates.TemplateResponse("video.html", {"request": request})


# Create tables at startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


def run_api():
    """Entry point for `poetry run start-api`."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,  # auto-reload in dev
    )


if __name__ == "__main__":
    run_api()
