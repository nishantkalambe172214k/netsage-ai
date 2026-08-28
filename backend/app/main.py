from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    init_db()
    
    # Auto-seed database if empty
    try:
        from app.core.database import SessionLocal
        from app.models.case import Case
        from app.services.case_loader import seed_cases
        from app.services.responsible_ai import seed_responsible_ai_examples

        db = SessionLocal()
        try:
            if db.query(Case).count() == 0:
                seed_cases(db)
                seed_responsible_ai_examples(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Auto-seed notification: {e}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NetSage AI - Cisco Packet Tracer Troubleshooting Assistant with Python Rule Checking & Mandatory Human Review",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to NetSage AI API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
