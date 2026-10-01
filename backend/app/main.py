import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.api import auth, users, patients, documents, events, timeline, signals, medications, investigations, search, dashboard, health

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Based Healthcare Journey Reconstruction - Research Prototype",
    version=settings.APP_VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Exception handlers
register_exception_handlers(app)

# Configure logging
configure_logging()

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(patients.router, prefix="/api", tags=["Patients"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(events.router, prefix="/api", tags=["Events"])
app.include_router(timeline.router, prefix="/api", tags=["Timeline"])
app.include_router(signals.router, prefix="/api", tags=["Signals"])
app.include_router(medications.router, prefix="/api", tags=["Medications"])
app.include_router(investigations.router, prefix="/api", tags=["Investigations"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
